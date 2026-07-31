"""Lightweight place-name -> IATA resolution, backing the flight search service.

Query understanding already normalizes free text into a clean city/country name
(see query_understanding.py), so this only needs to match that clean name against
the airport dataset rather than parse raw sentences.
"""

from functools import lru_cache

import airportsdata


@lru_cache
def _airports() -> dict:
    return airportsdata.load("IATA")


def resolve_iata(place: str | None) -> str | None:
    if not place:
        return None

    place = place.strip()
    if len(place) == 3 and place.isalpha():
        code = place.upper()
        if code in _airports():
            return code

    needle = place.lower()
    best: tuple[int, str] | None = None

    for iata, airport in _airports().items():
        city = str(airport.get("city", "")).lower()
        name = str(airport.get("name", "")).lower()

        score = 0
        if city == needle:
            score = 100
        elif needle in city:
            score = 60
        elif needle in name:
            score = 30

        if score and "international" in name:
            score += 10

        if score and (best is None or score > best[0]):
            best = (score, iata)

    return best[1] if best else None
