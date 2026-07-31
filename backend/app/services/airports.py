"""Lightweight place-name -> IATA resolution, backing the flight search service.

Query understanding already normalizes free text into a clean city/country name
(see query_understanding.py), so this only needs to match that clean name against
the airport dataset rather than parse raw sentences.
"""

from functools import lru_cache

import airportsdata

# Many major cities are served by several airports sharing the same `city`
# field in the dataset (e.g. "London" matches Heathrow, Gatwick, Luton,
# Stansted, City — and even London, Ontario). Without a preferred hub, plain
# name-matching picks whichever one the dataset happens to iterate to first,
# which is not necessarily the real primary hub. This overrides those cases
# for commonly-requested trip destinations.
PREFERRED_HUB = {
    "london": "LHR",
    "new york": "JFK",
    "paris": "CDG",
    "moscow": "SVO",
    "chicago": "ORD",
    "washington": "IAD",
    "tokyo": "NRT",
    "osaka": "KIX",
    "shanghai": "PVG",
    "beijing": "PEK",
    "milan": "MXP",
    "rome": "FCO",
    "istanbul": "IST",
    "houston": "IAH",
    "rio de janeiro": "GIG",
    "sao paulo": "GRU",
    "berlin": "BER",
    "seoul": "ICN",
    "bangkok": "BKK",
    "dubai": "DXB",
    "delhi": "DEL",
    "new delhi": "DEL",
    "mumbai": "BOM",
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "chennai": "MAA",
    "kolkata": "CCU",
    "hyderabad": "HYD",
    "pune": "PNQ",
    "toronto": "YYZ",
    "sydney": "SYD",
    "melbourne": "MEL",
    "singapore": "SIN",
    "kuala lumpur": "KUL",
    "jakarta": "CGK",
    "hong kong": "HKG",
    "amsterdam": "AMS",
    "madrid": "MAD",
    "barcelona": "BCN",
    "lisbon": "LIS",
    "vienna": "VIE",
    "zurich": "ZRH",
    "frankfurt": "FRA",
    "munich": "MUC",
    "athens": "ATH",
    "cairo": "CAI",
    "doha": "DOH",
    "abu dhabi": "AUH",
    "los angeles": "LAX",
    "san francisco": "SFO",
    "miami": "MIA",
    "boston": "BOS",
}


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

    if needle in PREFERRED_HUB:
        return PREFERRED_HUB[needle]

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
