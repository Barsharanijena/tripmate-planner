from app.graph.state import TravelState
from app.services.flights import search_flights


def flights_node(state: TravelState) -> dict:
    return {"flights": search_flights(state["query"])}
