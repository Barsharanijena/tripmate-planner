"""Weather grounding for the itinerary/packing steps — real numbers from
Open-Meteo (free, keyless), not an LLM guessing from pretrained knowledge.

Trip requests rarely include an exact date, so two real data sources are used
depending on what's known:
- No month mentioned: the live 7-day forecast for the destination, labeled as
  current conditions rather than a trip-date forecast (which would be a lie).
- A month mentioned ("in December"): actual historical daily data for that
  same month last year (or the most recently completed occurrence), which is
  a genuinely measured "typical" rather than a vibe.
"""

import calendar
from datetime import date
from statistics import mean

import requests

from app.schemas import WeatherSummary
from app.services.geocoding import geocode
from app.services.retry import retry_call

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def _condition_label(avg_high_c: float | None, precip_chance_pct: float | None) -> str:
    if avg_high_c is None:
        return "Conditions unavailable"

    if avg_high_c < 5:
        temp_label = "Cold"
    elif avg_high_c < 15:
        temp_label = "Cool"
    elif avg_high_c < 25:
        temp_label = "Mild"
    elif avg_high_c < 32:
        temp_label = "Warm"
    else:
        temp_label = "Hot"

    if precip_chance_pct is None:
        return temp_label
    if precip_chance_pct >= 50:
        return f"{temp_label} and rainy"
    if precip_chance_pct >= 20:
        return f"{temp_label} with a chance of rain"
    return f"{temp_label} and mostly dry"


def _most_recently_completed_month(month_name: str) -> tuple[date, date] | None:
    try:
        target_month = list(calendar.month_name).index(month_name.strip().capitalize())
    except ValueError:
        return None
    if target_month == 0:
        return None

    today = date.today()
    year = today.year
    if target_month >= today.month:
        year -= 1

    last_day = calendar.monthrange(year, target_month)[1]
    return date(year, target_month, 1), date(year, target_month, last_day)


def _fetch_forecast(lat: float, lon: float) -> WeatherSummary | None:
    def _call():
        response = requests.get(
            FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "forecast_days": 7,
                "timezone": "auto",
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    try:
        payload = retry_call(_call)
    except (requests.RequestException, ValueError):
        return None

    daily = payload.get("daily") or {}
    highs = [v for v in daily.get("temperature_2m_max", []) if v is not None]
    lows = [v for v in daily.get("temperature_2m_min", []) if v is not None]
    precip = [v for v in daily.get("precipitation_probability_max", []) if v is not None]

    if not highs or not lows:
        return None

    avg_high = round(mean(highs), 1)
    avg_low = round(mean(lows), 1)
    precip_chance = round(mean(precip), 1) if precip else None

    return WeatherSummary(
        basis="forecast",
        period_label="next 7 days",
        avg_high_c=avg_high,
        avg_low_c=avg_low,
        precipitation_chance_pct=precip_chance,
        condition_summary=_condition_label(avg_high, precip_chance),
    )


def _fetch_historical_average(lat: float, lon: float, month_name: str) -> WeatherSummary | None:
    date_range = _most_recently_completed_month(month_name)
    if not date_range:
        return None
    start, end = date_range

    def _call():
        response = requests.get(
            ARCHIVE_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                "timezone": "auto",
            },
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    try:
        payload = retry_call(_call)
    except (requests.RequestException, ValueError):
        return None

    daily = payload.get("daily") or {}
    highs = [v for v in daily.get("temperature_2m_max", []) if v is not None]
    lows = [v for v in daily.get("temperature_2m_min", []) if v is not None]
    precip = [v for v in daily.get("precipitation_sum", []) if v is not None]

    if not highs or not lows:
        return None

    avg_high = round(mean(highs), 1)
    avg_low = round(mean(lows), 1)
    rainy_days_pct = round(100 * sum(1 for v in precip if v > 1.0) / len(precip), 1) if precip else None

    return WeatherSummary(
        basis="historical_average",
        period_label=f"typical for {month_name.capitalize()} (based on {start.strftime('%B %Y')})",
        avg_high_c=avg_high,
        avg_low_c=avg_low,
        precipitation_chance_pct=rainy_days_pct,
        condition_summary=_condition_label(avg_high, rainy_days_pct),
    )


def get_weather(gateway_city: str, travel_month: str | None) -> WeatherSummary | None:
    location = geocode(gateway_city)
    if not location:
        return None

    if travel_month:
        result = _fetch_historical_average(location.lat, location.lon, travel_month)
        if result:
            return result
        # Bad/unparseable month name — fall through to a live forecast rather
        # than returning nothing.

    return _fetch_forecast(location.lat, location.lon)
