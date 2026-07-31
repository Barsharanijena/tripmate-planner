"""Lightweight place-name -> IATA resolution, backing the flight search service.

Query understanding already normalizes free text into a clean city/country name
(see query_understanding.py), so this only needs to match that clean name against
the airport dataset rather than parse raw sentences.
"""

import difflib
import re
from dataclasses import dataclass
from functools import lru_cache
from math import asin, cos, radians, sin, sqrt

import airportsdata

from app.services.geocoding import geocode

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
    # City-without-its-own-airport cases known to geocode badly or ambiguously:
    "panaji": "GOI",  # Goa's capital — geocoders often only index it as "Panjim"
    "goa": "GOI",
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


@dataclass
class AirportMatch:
    iata: str
    exact: bool
    matched_place: str | None = None
    """Geocoded place name the nearest-airport search actually centered on (only set when not exact)."""
    distance_km: float | None = None


@lru_cache
def _airports() -> dict:
    return airportsdata.load("IATA")


@lru_cache
def _city_names() -> tuple[str, ...]:
    return tuple({str(a.get("city", "")).lower() for a in _airports().values() if a.get("city")})


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r_earth_km = 6371.0
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * r_earth_km * asin(sqrt(a))


def _nearest_airport(lat: float, lon: float) -> tuple[str, float] | None:
    best: tuple[str, float] | None = None
    for iata, airport in _airports().items():
        try:
            distance = _haversine_km(lat, lon, float(airport["lat"]), float(airport["lon"]))
        except (KeyError, TypeError, ValueError):
            continue
        if best is None or distance < best[1]:
            best = (iata, distance)
    return best


def resolve_airport(place: str | None) -> AirportMatch | None:
    if not place:
        return None

    place = place.strip()
    needle = place.lower()

    # Curated aliases go first: a deliberately-checked city/country name
    # should always win over an incidental 3-letter collision with an
    # unrelated airport's actual IATA code (e.g. the city "Goa" is not the
    # airport code GOA — that's Genoa, Italy).
    if needle in PREFERRED_HUB:
        return AirportMatch(iata=PREFERRED_HUB[needle], exact=True)
    if needle in COUNTRY_HUB:
        return AirportMatch(iata=COUNTRY_HUB[needle], exact=True)

    if len(place) == 3 and place.isalpha():
        code = place.upper()
        if code in _airports():
            return AirportMatch(iata=code, exact=True)

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
        return AirportMatch(iata=best[1], exact=True)

    # Next: tolerate near-exact misspellings ("Bhubaneshwar" vs the dataset's
    # "Bhubaneswar", ratio ~0.96) by fuzzy-matching against known city names.
    # The cutoff is deliberately strict — looser thresholds (~0.8) also
    # confidently "correct" unrelated short names into real places that just
    # happen to be similarly spelled (e.g. "Narnia" -> "Sarnia", Ontario),
    # which is worse than admitting we don't recognize the place outright.
    close = difflib.get_close_matches(needle, _city_names(), n=1, cutoff=0.92)
    if close:
        return resolve_airport(close[0])

    # Last resort: the place doesn't match any airport or known alias by
    # name, but it might still be a real, small place without its own
    # airport (a town, a national park, a ski village). Geocoding to real
    # coordinates and finding the genuinely nearest airport by distance is a
    # fundamentally different, safer kind of guess than string similarity:
    # it's grounded in where the place actually is, not how its name looks,
    # and it fails closed for places that don't geocode to anything real
    # (fictional names, typos with no match) rather than confidently landing
    # on an unrelated place.
    location = geocode(place)
    if not location:
        return None

    nearest = _nearest_airport(location.lat, location.lon)
    if not nearest:
        return None

    iata, distance_km = nearest
    return AirportMatch(iata=iata, exact=False, matched_place=location.name, distance_km=round(distance_km, 1))


def resolve_iata(place: str | None) -> str | None:
    match = resolve_airport(place)
    return match.iata if match else None
