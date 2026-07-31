from typing import TypedDict

from app.schemas import FlightOption, HotelOption, ItineraryDay, TripQuery


class TravelState(TypedDict, total=False):
    user_message: str
    query: TripQuery
    flights: list[FlightOption]
    hotels: list[HotelOption]
    itinerary: list[ItineraryDay]
    trip_summary: str
    budget_estimate: str | None
    recommendations: list[str]
