"""Free, keyless geocoding via Open-Meteo — shared by airport resolution
(nearest-airport fallback) and the weather lookup.
"""

from dataclasses import dataclass

import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


@dataclass
class GeocodeResult:
    name: str
    country: str | None
    lat: float
    lon: float


def geocode(place: str) -> GeocodeResult | None:
    if not place or not place.strip():
        return None

    try:
        response = requests.get(
            GEOCODING_URL,
            params={"name": place.strip(), "count": 1, "language": "en", "format": "json"},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        return None

    results = payload.get("results") or []
    if not results:
        return None

    top = results[0]
    return GeocodeResult(name=top["name"], country=top.get("country"), lat=top["latitude"], lon=top["longitude"])
