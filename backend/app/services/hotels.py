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

Whenever a nightly rate is stated (e.g. "$120/night", "₹18,000 - ₹30,000 per night"), fill
BOTH price_estimate (the human-readable string, as found) AND the numeric
price_per_night_low/price_per_night_high/currency fields — those numeric fields drive a
real budget calculation downstream, so they matter as much as the display string. Use the
source's own currency (ISO code, e.g. "INR", "USD"), not a converted one.
"""


class _HotelShortlist(BaseModel):
    hotels: list[HotelOption] = Field(default_factory=list)


def search_hotels(query: TripQuery, refinement: str | None = None) -> list[HotelOption]:
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
    # "advanced" search depth and asking for price explicitly both matter a
    # lot here: the default "basic" depth mostly returns thin listicle/video
    # snippets with no real numbers, while "advanced" reliably surfaces
    # pages that actually state a nightly rate — which is what the budget
    # breakdown downstream depends on being real rather than invented.
    search = TavilySearch(max_results=5, search_depth="advanced")
    budget_hint = f" under ${query.budget_usd:.0f} total" if query.budget_usd else ""
    refinement_hint = f" {refinement}" if refinement else ""

    def _search_once():
        result = search.invoke(
            f"best hotels in {query.destination}{budget_hint}{refinement_hint} price per night for travelers"
        )
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

    refinement_line = f"\nTraveler feedback to prioritize: {refinement}" if refinement else ""

    try:
        structurer = get_llm(temperature=0).with_structured_output(_HotelShortlist)
        shortlist: _HotelShortlist = retry_call(
            lambda: structurer.invoke(
                [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(
                        content=f"Destination: {query.destination}{refinement_line}\n\nSearch results:\n{raw_results}"
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
