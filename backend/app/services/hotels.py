from langchain_core.messages import HumanMessage, SystemMessage
from langchain_tavily import TavilySearch
from pydantic import BaseModel, Field

from app.config import get_settings
from app.schemas import HotelOption, TripQuery
from app.services.llm import get_llm

SYSTEM_PROMPT = """You turn raw hotel search results into a short, structured shortlist.
Pick at most 4 distinct hotels. If price or rating isn't stated, leave it null rather than guessing.
"""


class _HotelShortlist(BaseModel):
    hotels: list[HotelOption] = Field(default_factory=list)


def search_hotels(query: TripQuery) -> list[HotelOption]:
    settings = get_settings()
    if not settings.tavily_api_key:
        return [
            HotelOption(
                name="Unavailable",
                summary="TAVILY_API_KEY is not configured; skipping hotel search.",
            )
        ]

    search = TavilySearch(max_results=5, api_key=settings.tavily_api_key)
    budget_hint = f" under ${query.budget_usd:.0f} total" if query.budget_usd else ""
    raw_results = search.invoke(f"best hotels in {query.destination}{budget_hint} for travelers")

    structurer = get_llm(temperature=0).with_structured_output(_HotelShortlist)
    shortlist = structurer.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Destination: {query.destination}\n\nSearch results:\n{raw_results}"),
        ]
    )

    return shortlist.hotels  # type: ignore[union-attr]
