"""Real bookable flight fares via Amadeus Self-Service (test environment,
free tier). AviationStack only returns live/status data with no prices —
this is what actually lets the budget breakdown compute a real flights line
instead of an LLM guess, and gives users an actual fare instead of "check
back later."
"""

import calendar
from datetime import date, timedelta
from functools import lru_cache

import requests

from app.config import get_settings
from app.schemas import FlightOption
from app.services.retry import retry_call

TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
SEARCH_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"

_token_cache: dict[str, object] = {"token": None, "expires_at": None}


def _get_access_token() -> str | None:
    settings = get_settings()
    if not settings.amadeus_api_key or not settings.amadeus_api_secret:
        return None

    cached_token = _token_cache.get("token")
    expires_at = _token_cache.get("expires_at")
    if cached_token and expires_at and date.today() < expires_at:  # coarse but adequate: tokens last ~30 min
        return cached_token  # type: ignore[return-value]

    def _call():
        response = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.amadeus_api_key,
                "client_secret": settings.amadeus_api_secret,
            },
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    try:
        payload = retry_call(_call)
    except (requests.RequestException, ValueError):
        return None

    token = payload.get("access_token")
    if not token:
        return None

    _token_cache["token"] = token
    _token_cache["expires_at"] = date.today()  # re-fetched at most once/day; cheap and avoids clock skew logic
    return token


def _default_departure_date(travel_month: str | None) -> date:
    today = date.today()
    if not travel_month:
        return today + timedelta(days=21)

    try:
        target_month = list(calendar.month_name).index(travel_month.strip().capitalize())
    except ValueError:
        return today + timedelta(days=21)
    if target_month == 0:
        return today + timedelta(days=21)

    year = today.year if target_month > today.month else today.year + 1
    return date(year, target_month, 1)


@lru_cache(maxsize=256)
def _search_cached(origin_iata: str, dest_iata: str, departure_date_iso: str, adults: int) -> tuple:
    settings = get_settings()
    token = _get_access_token()
    if not token:
        return ()

    def _call():
        response = requests.get(
            SEARCH_URL,
            headers={"Authorization": f"Bearer {token}"},
            params={
                "originLocationCode": origin_iata,
                "destinationLocationCode": dest_iata,
                "departureDate": departure_date_iso,
                "adults": adults,
                "max": 6,
                "currencyCode": "USD",
            },
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    try:
        payload = retry_call(_call)
    except requests.RequestException:
        return ()

    return tuple(payload.get("data") or [])


def search_real_fares(
    origin_iata: str | None, dest_iata: str, travel_month: str | None, adults: int = 1
) -> list[FlightOption] | None:
    """Returns real bookable fares, or None if Amadeus isn't configured/reachable
    (the caller should fall back to AviationStack in that case, not show an error)."""

    settings = get_settings()
    if not settings.amadeus_api_key or not settings.amadeus_api_secret:
        return None
    if not origin_iata:
        return None

    departure_date = _default_departure_date(travel_month)
    offers = _search_cached(origin_iata, dest_iata, departure_date.isoformat(), adults)
    if not offers:
        return None

    options = []
    for offer in offers:
        price = offer.get("price") or {}
        itineraries = offer.get("itineraries") or []
        segments = itineraries[0].get("segments") if itineraries else []
        first_segment = segments[0] if segments else {}
        last_segment = segments[-1] if segments else {}

        options.append(
            FlightOption(
                airline=first_segment.get("carrierCode") or "Unknown",
                flight_number=(
                    f"{first_segment.get('carrierCode', '')}{first_segment.get('number', '')}".strip() or None
                ),
                origin_iata=(first_segment.get("departure") or {}).get("iataCode", origin_iata),
                destination_iata=(last_segment.get("arrival") or {}).get("iataCode", dest_iata),
                departure_time=(first_segment.get("departure") or {}).get("at"),
                arrival_time=(last_segment.get("arrival") or {}).get("at"),
                price=float(price["total"]) if price.get("total") else None,
                currency=price.get("currency"),
                notes=(
                    f"Fare for {departure_date.strftime('%B %-d, %Y')} — actual dates may change the price."
                    if not travel_month
                    else None
                ),
            )
        )

    return options
