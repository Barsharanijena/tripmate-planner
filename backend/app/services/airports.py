"""Lightweight place-name -> IATA resolution, backing the flight search service.

Query understanding already normalizes free text into a clean city/country name
(see query_understanding.py), so this only needs to match that clean name against
the airport dataset rather than parse raw sentences.
"""

import difflib
import re
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
    "bhubaneswar": "BBI",
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

# Query understanding sometimes hands back a country rather than a city
# ("plan a trip to China") — these route to that country's primary
# international gateway rather than falling through to name-matching, where
# a bare country name can accidentally substring-match an unrelated airport
# (e.g. "china" inside "Chistochina", a small airport in Alaska).
COUNTRY_HUB = {
    "china": "PEK",
    "japan": "NRT",
    "india": "DEL",
    "usa": "JFK",
    "united states": "JFK",
    "united states of america": "JFK",
    "uk": "LHR",
    "united kingdom": "LHR",
    "england": "LHR",
    "france": "CDG",
    "germany": "FRA",
    "italy": "FCO",
    "spain": "MAD",
    "portugal": "LIS",
    "russia": "SVO",
    "canada": "YYZ",
    "australia": "SYD",
    "brazil": "GRU",
    "mexico": "MEX",
    "south korea": "ICN",
    "korea": "ICN",
    "thailand": "BKK",
    "vietnam": "SGN",
    "indonesia": "CGK",
    "malaysia": "KUL",
    "singapore": "SIN",
    "philippines": "MNL",
    "uae": "DXB",
    "united arab emirates": "DXB",
    "qatar": "DOH",
    "saudi arabia": "JED",
    "turkey": "IST",
    "egypt": "CAI",
    "greece": "ATH",
    "netherlands": "AMS",
    "switzerland": "ZRH",
    "austria": "VIE",
    "nepal": "KTM",
    "sri lanka": "CMB",
    "bangladesh": "DAC",
    "pakistan": "ISB",
    "new zealand": "AKL",
    "south africa": "JNB",
}


@lru_cache
def _airports() -> dict:
    return airportsdata.load("IATA")


@lru_cache
def _city_names() -> tuple[str, ...]:
    return tuple({str(a.get("city", "")).lower() for a in _airports().values() if a.get("city")})


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
    if needle in COUNTRY_HUB:
        return COUNTRY_HUB[needle]

    needle_pattern = re.compile(rf"\b{re.escape(needle)}\b")
    best: tuple[int, str] | None = None

    for iata, airport in _airports().items():
        city = str(airport.get("city", "")).lower()
        name = str(airport.get("name", "")).lower()

        score = 0
        if city == needle:
            score = 100
        elif needle_pattern.search(city):
            score = 60
        elif needle_pattern.search(name):
            score = 30

        if score and "international" in name:
            score += 10

        if score and (best is None or score > best[0]):
            best = (score, iata)

    if best:
        return best[1]

    # Last resort: tolerate minor misspellings ("Bhubaneshwar" vs the
    # dataset's "Bhubaneswar") by fuzzy-matching against known city names.
    close = difflib.get_close_matches(needle, _city_names(), n=1, cutoff=0.8)
    if close:
        return resolve_iata(close[0])

    return None
