import requests

from app.config import get_settings
from app.schemas import FlightOption, TripQuery
from app.services.airports import resolve_iata

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

    origin_iata = resolve_iata(query.origin)
    dest_iata = resolve_iata(query.destination)

    params = {"access_key": settings.aviationstack_api_key, "limit": limit}
    if origin_iata:
        params["dep_iata"] = origin_iata
    if dest_iata:
        params["arr_iata"] = dest_iata

    try:
        response = requests.get(AVIATIONSTACK_URL, params=params, timeout=20)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        return [FlightOption(airline="Error", notes=f"Flight API request failed: {exc}")]

    if "error" in payload:
        message = payload["error"].get("message", "Unknown error")
        return [FlightOption(airline="Error", notes=f"Flight API error: {message}")]

    flights = payload.get("data") or []
    if not flights:
        return [
            FlightOption(
                airline="No live matches",
                origin_iata=origin_iata,
                destination_iata=dest_iata,
                notes="AviationStack returns live/status flights, not fares. Try a broader route or check back later.",
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
            )
        )

    return options
