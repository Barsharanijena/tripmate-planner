"""Domain models shared across the graph, services, and API layer."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

AgentStep = Literal["understand", "flights", "hotels", "itinerary", "final"]
StepStatus = Literal["started", "completed", "failed"]


class TripRequest(BaseModel):
    message: str = Field(min_length=1, description="Free-text trip request from the user")
    thread_id: str | None = Field(default=None, description="Existing conversation to continue")


class TripQuery(BaseModel):
    """Structured intent extracted from the user's free-text request."""

    origin: str | None = Field(default=None, description="Origin city or country, if mentioned")
    destination: str = Field(description="Destination city or country")
    trip_length_days: int | None = Field(default=None, ge=1, le=60)
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
    notes: str | None = None


class HotelOption(BaseModel):
    name: str
    area: str | None = None
    price_estimate: str | None = None
    rating: str | None = None
    summary: str
    source_url: str | None = None


class ItineraryDay(BaseModel):
    day_number: int
    title: str
    activities: list[str]


class TravelPlan(BaseModel):
    destination: str
    origin: str | None = None
    trip_summary: str
    flights: list[FlightOption] = Field(default_factory=list)
    hotels: list[HotelOption] = Field(default_factory=list)
    itinerary: list[ItineraryDay] = Field(default_factory=list)
    budget_estimate: str | None = None
    recommendations: list[str] = Field(default_factory=list)


class AgentStepEvent(BaseModel):
    """One line of a server-sent event stream describing graph progress."""

    type: Literal["step", "result", "error"]
    step: AgentStep | None = None
    status: StepStatus | None = None
    message: str | None = None
    thread_id: str | None = None
    plan: TravelPlan | None = None
