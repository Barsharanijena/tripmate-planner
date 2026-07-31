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
            params={"name": place.strip(), "count": 10, "language": "en", "format": "json"},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        return None

    results = payload.get("results") or []
    if not results:
        return None

    # The API's own ranking sometimes puts a same-named tiny village ahead of
    # a genuinely well-known city (e.g. "Panaji" matched a hamlet in
    # Guatemala with no population data before India's actual state capital
    # of ~71k people, which the source only indexes under its historic name
    # "Panjim"). Preferring the highest population among the candidates it
    # did return is a cheap, general fix for that whole class of mismatch.
    best = max(results, key=lambda r: r.get("population") or 0)
    return GeocodeResult(name=best["name"], country=best.get("country"), lat=best["latitude"], lon=best["longitude"])
