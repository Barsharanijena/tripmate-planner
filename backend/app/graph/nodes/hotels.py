from app.graph.state import TravelState
from app.services.hotels import search_hotels


def hotels_node(state: TravelState) -> dict:
    return {"hotels": search_hotels(state["query"])}
