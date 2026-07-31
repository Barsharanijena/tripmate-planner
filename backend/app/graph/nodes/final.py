from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.graph.state import TravelState
from app.services.llm import get_llm

SYSTEM_PROMPT = """You write the closing summary for a travel plan that already has
flights, hotels, and a day-by-day itinerary attached. Produce:
- trip_summary: 2-3 sentences, warm and practical.
- budget_estimate: a short range string like "$800-1100", or null if not estimable.
- recommendations: 2-4 short, concrete tips (packing, timing, booking advice).
"""


class _FinalTouches(BaseModel):
    trip_summary: str
    budget_estimate: str | None = None
    recommendations: list[str] = Field(default_factory=list)


def final_node(state: TravelState) -> dict:
    query = state["query"]
    context = (
        f"Destination: {query.destination}\n"
        f"Budget (USD): {query.budget_usd or 'unspecified'}\n\n"
        f"Flights: {state['flights']}\n\n"
        f"Hotels: {state['hotels']}\n\n"
        f"Itinerary: {state['itinerary']}\n"
    )

    llm = get_llm(temperature=0.4).with_structured_output(_FinalTouches)
    result: _FinalTouches = llm.invoke(
        [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=context)]
    )  # type: ignore[assignment]

    return {
        "trip_summary": result.trip_summary,
        "budget_estimate": result.budget_estimate,
        "recommendations": result.recommendations,
    }
