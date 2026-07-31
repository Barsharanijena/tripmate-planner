from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.graph.state import TravelState
from app.schemas import ItineraryDay
from app.services.llm import get_llm

SYSTEM_PROMPT = """You are an expert travel planner. Build a practical, budget-aware
day-by-day itinerary from the trip details, flights, and hotel shortlist provided.
Keep each day to 3-5 concrete activities. If trip length is unknown, default to 3 days.
"""


class _Itinerary(BaseModel):
    days: list[ItineraryDay] = Field(default_factory=list)


def itinerary_node(state: TravelState) -> dict:
    query = state["query"]
    context = (
        f"Destination: {query.destination}\n"
        f"Origin: {query.origin}\n"
        f"Trip length (days): {query.trip_length_days or 'unspecified'}\n"
        f"Travelers: {query.travelers}\n"
        f"Budget (USD): {query.budget_usd or 'unspecified'}\n"
        f"Preferences: {', '.join(query.preferences) or 'none stated'}\n\n"
        f"Flight options:\n{state['flights']}\n\n"
        f"Hotel shortlist:\n{state['hotels']}\n"
    )

    llm = get_llm(temperature=0.4).with_structured_output(_Itinerary)
    result = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=context)])

    return {"itinerary": result.days}  # type: ignore[union-attr]
