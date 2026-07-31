"""Turns a free-text trip request into structured intent.

The reference implementation this project is inspired by resolved routes with a large
hand-written regex/alias table. Doing that parsing with a structured-output LLM call
instead is more robust to phrasing and needs no maintained alias list.
"""

from langchain_core.messages import HumanMessage, SystemMessage

from app.config import get_settings
from app.schemas import TripQuery
from app.services.llm import get_llm

SYSTEM_PROMPT = """You extract structured trip intent from a traveler's free-text request.
- If no origin is mentioned, leave it null.
- trip_length_days should be null if not stated or inferable.
- preferences should be short tags like "beaches", "museums", "nightlife", "budget-friendly".
- gateway_city must always be one real, flyable city — never a region, state, country,
  or multi-city area. If the destination as phrased already is one city, gateway_city is
  the same city. Otherwise pick its actual primary gateway, e.g. "Kashmir" -> "Srinagar",
  "Tuscany" -> "Florence", "the Maldives" -> "Male", "Japan" -> "Tokyo".
"""


def parse_trip_query(message: str) -> TripQuery:
    settings = get_settings()
    llm = get_llm(temperature=0).with_structured_output(TripQuery)

    result = llm.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=message),
        ]
    )

    query: TripQuery = result  # type: ignore[assignment]
    if not query.origin:
        query.origin = settings.default_origin_city

    return query
