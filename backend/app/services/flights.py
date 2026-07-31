import requests

from app.config import get_settings
from app.schemas import FlightOption, TripQuery
from app.services.airports import resolve_airport
from app.services.retry import retry_call

AVIATIONSTACK_URL = "https://api.aviationstack.com/v1/flights"


def search_flights(query: TripQuery, limit: int = 6) -> list[FlightOption]:
    settings = get_settings()
    if not settings.aviationstack_api_key:
        return [
            FlightOption(
                airline="Unavailable",
                notes="AVIATIONSTACK_API_KEY is not configured; skipping live flight search.",
            )
        ]

    origin_match = resolve_airport(query.origin)
    # gateway_city is always a single real city (query understanding resolves
    # regions/states/countries down to their primary gateway, e.g. "Kashmir"
    # -> "Srinagar"), so lookups use it instead of the free-text destination.
    dest_match = resolve_airport(query.gateway_city)

    # Without a resolved destination, AviationStack would be queried with no
    # route filter at all and hand back arbitrary global live flights that
    # look plausible but have nothing to do with what was actually asked —
    # worse than no result, so this stops before making that call.
    if not dest_match:
        return [
            FlightOption(
                airline="Unknown destination",
                origin_iata=origin_match.iata if origin_match else None,
                notes=(
                    f'Couldn\'t match "{query.gateway_city}" to a known airport, city, or '
                    "country — live flight search was skipped rather than showing unrelated flights."
                ),
            )
        ]

    origin_iata = origin_match.iata if origin_match else None
    dest_iata = dest_match.iata

    fallback_note = None
    if not dest_match.exact:
        fallback_note = (
            f'"{query.gateway_city}" doesn\'t have its own airport — showing the nearest one, '
            f"{dest_iata} near {dest_match.matched_place} (~{dest_match.distance_km:.0f} km away)."
        )
    if origin_match and not origin_match.exact:
        origin_note = (
            f'Origin "{query.origin}" doesn\'t have its own airport — using the nearest one, '
            f"{origin_iata} near {origin_match.matched_place} (~{origin_match.distance_km:.0f} km away)."
        )
        fallback_note = f"{fallback_note} {origin_note}" if fallback_note else origin_note

    params = {"access_key": settings.aviationstack_api_key, "limit": limit, "arr_iata": dest_iata}
    if origin_iata:
        params["dep_iata"] = origin_iata

    def _fetch():
        response = requests.get(AVIATIONSTACK_URL, params=params, timeout=20)
        response.raise_for_status()
        return response.json()

    try:
        payload = retry_call(_fetch)
    except requests.RequestException as exc:
        return [FlightOption(airline="Error", notes=f"Flight API request failed after retries: {exc}")]
    except ValueError:
        return [FlightOption(airline="Error", notes="Flight API returned an unreadable response.")]

    if "error" in payload:
        message = payload["error"].get("message", "Unknown error")
        return [FlightOption(airline="Error", notes=f"Flight API error: {message}")]

    no_matches_note = "AviationStack returns live/status flights, not fares. Try a broader route or check back later."

    flights = payload.get("data") or []
    if not flights:
        return [
            FlightOption(
                airline="No live matches",
                origin_iata=origin_iata,
                destination_iata=dest_iata,
                notes=f"{fallback_note} {no_matches_note}" if fallback_note else no_matches_note,
            )
        ]

    options = []
    for flight in flights[:limit]:
        airline = (flight.get("airline") or {}).get("name") or "Unknown airline"
        flight_number = (flight.get("flight") or {}).get("iata")
        departure = flight.get("departure") or {}
        arrival = flight.get("arrival") or {}

        options.append(
            FlightOption(
                airline=airline,
                flight_number=flight_number,
                origin_iata=departure.get("iata") or origin_iata,
                destination_iata=arrival.get("iata") or dest_iata,
                departure_time=departure.get("scheduled"),
                arrival_time=arrival.get("scheduled"),
                status=flight.get("flight_status"),
                # Only the first card carries the fallback disclaimer, to
                # avoid repeating it on every row.
                notes=fallback_note if fallback_note and not options else None,
            )
        )

    return options
