"""Domain models shared across the graph, services, and API layer."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

AgentStep = Literal["understand", "flights", "hotels", "weather", "itinerary", "final"]
StepStatus = Literal["started", "completed", "failed"]


class TripRequest(BaseModel):
    message: str = Field(min_length=1, description="Free-text trip request from the user")
    thread_id: str | None = Field(default=None, description="Existing conversation to continue")


class RefineRequest(BaseModel):
    instruction: str = Field(min_length=1, description="e.g. 'cheaper hotels', 'make day 2 more relaxed'")


class TripQuery(BaseModel):
    """Structured intent extracted from the user's free-text request."""

    origin: str | None = Field(default=None, description="Origin city or country, if mentioned")
    destination: str = Field(description="Destination as the user phrased it, for display")
    gateway_city: str = Field(
        description=(
            "A single real, flyable city for this trip — the destination itself if it's "
            "already one city, otherwise its primary gateway (e.g. 'Kashmir' -> 'Srinagar', "
            "'Tuscany' -> 'Florence'). Used for flight/hotel lookups, so it must be a real city."
        )
    )
    trip_length_days: int | None = Field(default=None, ge=1, le=60)
    travel_month: str | None = Field(
        default=None,
        description="Full month name if the user gave any timing hint (e.g. 'next April' -> 'April'), else null",
    )
    travelers: int = Field(default=1, ge=1)
    budget_usd: float | None = Field(default=None, ge=0)
    preferences: list[str] = Field(default_factory=list, description="e.g. 'beaches', 'museums', 'budget-friendly'")


class FlightOption(BaseModel):
    airline: str
    flight_number: str | None = None
    origin_iata: str | None = None
    destination_iata: str | None = None
    departure_time: str | None = None
    arrival_time: str | None = None
    status: str | None = None
    price: float | None = Field(default=None, description="Real bookable total fare, when sourced from Amadeus")
    currency: str | None = None
    notes: str | None = None


class HotelOption(BaseModel):
    name: str
    area: str | None = None
    price_estimate: str | None = None
    price_per_night_low: float | None = Field(
        default=None, description="Numeric low end of nightly price if stated in the source, else null"
    )
    price_per_night_high: float | None = Field(
        default=None, description="Numeric high end of nightly price if stated in the source, else null"
    )
    currency: str | None = Field(default=None, description="ISO code, e.g. 'USD', 'INR', if a price was found")
    rating: str | None = None
    summary: str
    source_url: str | None = None


class ItineraryDay(BaseModel):
    day_number: int
    title: str
    activities: list[str]


class WeatherSummary(BaseModel):
    basis: Literal["forecast", "historical_average"]
    period_label: str = Field(description="e.g. 'next 7 days' or 'typical for December'")
    avg_high_c: float | None = None
    avg_low_c: float | None = None
    precipitation_chance_pct: float | None = None
    condition_summary: str = Field(description="Short human label, e.g. 'Cold and mostly dry'")


class BudgetLine(BaseModel):
    category: Literal["flights", "hotels", "food", "activities", "other"]
    amount_low: float | None = None
    amount_high: float | None = None
    currency: str = "USD"
    basis: Literal["sourced", "estimated"] = Field(
        description="'sourced' when computed from real prices this app already found, 'estimated' when an LLM guess"
    )
    note: str | None = None


class TravelPlan(BaseModel):
    destination: str
    origin: str | None = None
    trip_summary: str
    flights: list[FlightOption] = Field(default_factory=list)
    hotels: list[HotelOption] = Field(default_factory=list)
    weather: WeatherSummary | None = None
    itinerary: list[ItineraryDay] = Field(default_factory=list)
    budget: list[BudgetLine] = Field(default_factory=list)
    packing_tips: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class AgentStepEvent(BaseModel):
    """One line of a server-sent event stream describing graph progress."""

    type: Literal["step", "result", "error"]
    step: AgentStep | None = None
    status: StepStatus | None = None
    message: str | None = None
    thread_id: str | None = None
    plan: TravelPlan | None = None
