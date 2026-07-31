import uuid
from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.graph.checkpoint import get_checkpointer
from app.graph.nodes.final import final_node
from app.graph.nodes.flights import flights_node
from app.graph.nodes.hotels import hotels_node
from app.graph.nodes.itinerary import itinerary_node
from app.graph.nodes.understand import understand_node
from app.graph.state import TravelState
from app.schemas import TravelPlan, TripQuery


@lru_cache
def get_travel_graph():
    graph = StateGraph(TravelState)

    graph.add_node("understand", understand_node)
    graph.add_node("flights", flights_node)
    graph.add_node("hotels", hotels_node)
    graph.add_node("itinerary", itinerary_node)
    graph.add_node("final", final_node)

    graph.add_edge(START, "understand")
    # Flights and hotels don't depend on each other, so they fan out and run
    # concurrently; itinerary is a fan-in that waits on both branches.
    graph.add_edge("understand", "flights")
    graph.add_edge("understand", "hotels")
    graph.add_edge("flights", "itinerary")
    graph.add_edge("hotels", "itinerary")
    graph.add_edge("itinerary", "final")
    graph.add_edge("final", END)

    return graph.compile(checkpointer=get_checkpointer())


def new_thread_id() -> str:
    return f"trip_{uuid.uuid4().hex[:12]}"


def state_to_plan(state: TravelState, query: TripQuery) -> TravelPlan:
    return TravelPlan(
        destination=query.destination,
        origin=query.origin,
        trip_summary=state.get("trip_summary", ""),
        flights=state.get("flights", []),
        hotels=state.get("hotels", []),
        itinerary=state.get("itinerary", []),
        budget_estimate=state.get("budget_estimate"),
        recommendations=state.get("recommendations", []),
    )
