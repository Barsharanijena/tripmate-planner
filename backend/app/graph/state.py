from typing import TypedDict

from app.schemas import BudgetLine, FlightOption, HotelOption, ItineraryDay, TripQuery, WeatherSummary


class TravelState(TypedDict, total=False):
    user_message: str
    query: TripQuery
    refinement_instruction: str | None
    """Transient: set only while re-running a node for a refine request, never during a normal run."""
    flights: list[FlightOption]
    hotels: list[HotelOption]
    weather: WeatherSummary | None
    itinerary: list[ItineraryDay]
    trip_summary: str
    budget: list[BudgetLine]
    packing_tips: list[str]
    recommendations: list[str]
