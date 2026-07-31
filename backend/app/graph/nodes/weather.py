from app.graph.state import TravelState
from app.services.weather import get_weather


def weather_node(state: TravelState) -> dict:
    query = state["query"]
    # A lookup failure here (unusual — geocoding covers virtually any real
    # place) just means no weather context for itinerary/packing, not a
    # reason to fail the trip plan.
    weather = get_weather(query.gateway_city, query.travel_month)
    return {"weather": weather}
