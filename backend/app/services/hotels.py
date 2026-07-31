import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_tavily import TavilySearch
from pydantic import BaseModel, Field

from app.config import get_settings
from app.schemas import HotelOption, TripQuery
from app.services.llm import get_llm
from app.services.retry import retry_call

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

    # TavilySearch reads its key from the process environment rather than a
    # constructor kwarg, so it has to be exported here rather than passed in.
    os.environ.setdefault("TAVILY_API_KEY", settings.tavily_api_key)
    search = TavilySearch(max_results=5)
    budget_hint = f" under ${query.budget_usd:.0f} total" if query.budget_usd else ""

    def _search_once():
        result = search.invoke(f"best hotels in {query.destination}{budget_hint} for travelers")
        # TavilySearch catches its own request errors and returns {"error": ...}
        # instead of raising, so that has to be promoted back into a real
        # exception for retry_call to retry and for the except below to catch.
        if isinstance(result, dict) and result.get("error"):
            raise RuntimeError(str(result["error"]))
        return result

    try:
        raw_results = retry_call(_search_once)
    except Exception as exc:  # noqa: BLE001 - surfaced to the user, not a crash
        return [
            HotelOption(
                name="Search failed",
                summary=f"Hotel search is temporarily unavailable: {exc}",
            )
        ]

    try:
        structurer = get_llm(temperature=0).with_structured_output(_HotelShortlist)
        shortlist: _HotelShortlist = retry_call(
            lambda: structurer.invoke(
                [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(
                        content=f"Destination: {query.destination}\n\nSearch results:\n{raw_results}"
                    ),
                ]
            )
        )  # type: ignore[assignment]
    except Exception as exc:  # noqa: BLE001
        return [
            HotelOption(
                name="Summary unavailable",
                summary=f"Found hotel results but couldn't summarize them: {exc}",
            )
        ]

    return shortlist.hotels
