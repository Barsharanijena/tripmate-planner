from app.graph.state import TravelState
from app.services.query_understanding import parse_trip_query
from app.services.retry import retry_call


def understand_node(state: TravelState) -> dict:
    # Unlike the other nodes, a failure here is fatal to the whole request —
    # without a parsed destination there's nothing for flights/hotels/itinerary
    # to work with, so this one is allowed to propagate (and retried harder).
    query = retry_call(lambda: parse_trip_query(state["user_message"]), attempts=3)
    return {"query": query}
