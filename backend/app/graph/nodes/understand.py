from app.graph.state import TravelState
from app.services.query_understanding import parse_trip_query


def understand_node(state: TravelState) -> dict:
    query = parse_trip_query(state["user_message"])
    return {"query": query}
