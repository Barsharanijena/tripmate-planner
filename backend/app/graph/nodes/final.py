from collections import Counter

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.graph.state import TravelState
from app.schemas import BudgetLine, FlightOption, HotelOption
from app.services.llm import get_llm
from app.services.retry import retry_call

SYSTEM_PROMPT = """You write the closing touches for a travel plan that already has
flights, hotels, weather, and a day-by-day itinerary attached.

Real budgets may already be computed from sourced data for some categories (you'll be
told which) — never estimate those yourself, only the ones still missing. Produce, in
the given currency:
- trip_summary: 2-3 sentences, warm and practical.
- flights_budget / food_budget / activities_budget: your best estimate for whichever of
  these aren't already sourced, as plain numbers in the stated currency (no symbols),
  with a short note on what it's based on. Leave amounts null if genuinely not
  estimable, and null out any category that's already sourced.
- packing_tips: 2-4 concrete items grounded in the actual weather data given
  (temperatures, rain chance) — not generic "pack layers" filler.
- recommendations: 2-4 short, concrete tips (timing, booking advice, local
  know-how) distinct from the packing tips.
"""


class _CategoryEstimate(BaseModel):
    amount_low: float | None = None
    amount_high: float | None = None
    note: str | None = None


class _FinalTouches(BaseModel):
    trip_summary: str
    flights_budget: _CategoryEstimate = Field(default_factory=_CategoryEstimate)
    food_budget: _CategoryEstimate = Field(default_factory=_CategoryEstimate)
    activities_budget: _CategoryEstimate = Field(default_factory=_CategoryEstimate)
    packing_tips: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


def _hotels_budget_line(hotels: list[HotelOption], nights: int) -> BudgetLine | None:
    priced = [h for h in hotels if h.price_per_night_low is not None or h.price_per_night_high is not None]
    if not priced:
        return None

    # Different source pages can quote different currencies for the same
    # search (booking sites often auto-localize by server region) — mixing
    # them in one min/max would silently produce a nonsense range, so only
    # the majority currency's listings are used for the real computed line.
    currency = Counter(h.currency for h in priced if h.currency).most_common(1)[0][0]
    same_currency = [h for h in priced if h.currency == currency]
    dropped = len(priced) - len(same_currency)

    lows = [
        h.price_per_night_low if h.price_per_night_low is not None else h.price_per_night_high
        for h in same_currency
    ]
    highs = [
        h.price_per_night_high if h.price_per_night_high is not None else h.price_per_night_low
        for h in same_currency
    ]

    note = f"{nights} night(s) at the nightly rates found above"
    if dropped:
        note += f" ({dropped} listing(s) in a different currency excluded from this total)"

    return BudgetLine(
        category="hotels",
        amount_low=round(min(lows) * nights, 2),
        amount_high=round(max(highs) * nights, 2),
        currency=currency,
        basis="sourced",
        note=note,
    )


def _flights_budget_line(flights: list[FlightOption]) -> BudgetLine | None:
    priced = [f for f in flights if f.price is not None]
    if not priced:
        return None

    currency = Counter(f.currency for f in priced if f.currency).most_common(1)[0][0]
    same_currency = [f.price for f in priced if f.currency == currency]

    return BudgetLine(
        category="flights",
        amount_low=round(min(same_currency), 2),
        amount_high=round(max(same_currency), 2),
        currency=currency,
        basis="sourced",
        note="Real bookable fares found above",
    )


def _category_line(category: str, estimate: _CategoryEstimate, currency: str) -> BudgetLine | None:
    if estimate.amount_low is None and estimate.amount_high is None:
        return None
    return BudgetLine(
        category=category,
        amount_low=estimate.amount_low,
        amount_high=estimate.amount_high,
        currency=currency,
        basis="estimated",
        note=estimate.note,
    )


def final_node(state: TravelState) -> dict:
    query = state["query"]
    nights = max(query.trip_length_days - 1, 1) if query.trip_length_days else 3
    hotels_line = _hotels_budget_line(state.get("hotels", []), nights)
    flights_line = _flights_budget_line(state.get("flights", []))
    currency = (hotels_line or flights_line).currency if (hotels_line or flights_line) else "USD"

    sourced_categories = [c for c, line in [("flights", flights_line), ("hotels", hotels_line)] if line]

    weather = state.get("weather")
    weather_context = (
        f"{weather.condition_summary}, avg high {weather.avg_high_c}C / low {weather.avg_low_c}C, "
        f"{weather.precipitation_chance_pct}% chance of rain ({weather.period_label})"
        if weather
        else "unavailable"
    )

    context = (
        f"Destination: {query.destination}\n"
        f"Budget (USD, as the traveler stated it): {query.budget_usd or 'unspecified'}\n"
        f"Currency to use for your estimates: {currency}\n"
        f"Already sourced (do NOT estimate these): {sourced_categories or 'none'}\n"
        f"Nights: {nights}\n"
        f"Weather: {weather_context}\n\n"
        f"Flights: {state.get('flights')}\n"
        f"(Real flights budget already computed: {flights_line})\n\n"
        f"Hotels: {state.get('hotels')}\n"
        f"(Real hotels budget already computed: {hotels_line})\n\n"
        f"Itinerary: {state.get('itinerary')}\n"
    )

    llm = get_llm(temperature=0.4).with_structured_output(_FinalTouches)

    try:
        result: _FinalTouches = retry_call(
            lambda: llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=context)])
        )  # type: ignore[assignment]
    except Exception as exc:  # noqa: BLE001 - the flights/hotels/itinerary already gathered still ship
        return {
            "trip_summary": (
                f"Here's what we found for your trip to {query.destination}. "
                f"We couldn't generate a polished summary right now ({exc}), but the "
                "flights, hotels, and itinerary above are ready."
            ),
            "budget": [line for line in [flights_line, hotels_line] if line],
            "packing_tips": [],
            "recommendations": [],
        }

    budget = [line for line in [flights_line, hotels_line] if line]
    for category, estimate in [
        ("flights", result.flights_budget),
        ("food", result.food_budget),
        ("activities", result.activities_budget),
    ]:
        if category in sourced_categories:
            continue
        line = _category_line(category, estimate, currency)
        if line:
            budget.append(line)

    return {
        "trip_summary": result.trip_summary,
        "budget": budget,
        "packing_tips": result.packing_tips,
        "recommendations": result.recommendations,
    }
