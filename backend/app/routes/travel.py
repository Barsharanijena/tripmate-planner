import asyncio
import queue
import threading
from collections.abc import AsyncIterator
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from app.graph.build import get_travel_graph, new_thread_id, state_to_plan
from app.graph.nodes.final import final_node
from app.graph.nodes.itinerary import itinerary_node
from app.schemas import AgentStepEvent, RefineRequest, TravelPlan, TripRequest
from app.services.hotels import search_hotels
from app.services.llm import get_llm
from app.services.retry import retry_call

router = APIRouter()

STEP_MESSAGES = {
    "understand": "Reading your request",
    "flights": "Searching flights",
    "hotels": "Researching hotels",
    "weather": "Checking the weather",
    "itinerary": "Building your day-by-day itinerary",
    "final": "Finalizing your trip plan",
}

_DONE = object()


async def _stream_events(request: TripRequest) -> AsyncIterator[AgentStepEvent]:
    """Runs the (blocking) graph in a worker thread and relays events as they arrive.

    LangGraph node functions here do blocking network/LLM calls, so driving
    graph.stream() directly on the event loop would stall every other request.
    A background thread plus a queue keeps the server responsive while still
    giving the client live per-node progress.
    """

    graph = get_travel_graph()
    thread_id = request.thread_id or new_thread_id()
    config = {"configurable": {"thread_id": thread_id}}
    events: queue.Queue = queue.Queue()

    def worker() -> None:
        last_state: dict = {}
        try:
            for update in graph.stream(
                {"user_message": request.message}, config=config, stream_mode="updates"
            ):
                for node_name, node_output in update.items():
                    last_state.update(node_output)
                    events.put(
                        AgentStepEvent(
                            type="step",
                            step=node_name,
                            status="completed",
                            message=STEP_MESSAGES.get(node_name, node_name),
                            thread_id=thread_id,
                        )
                    )

            query = last_state.get("query")
            if query is None:
                raise RuntimeError("Graph finished without producing trip intent")

            plan = state_to_plan(last_state, query)
            events.put(AgentStepEvent(type="result", thread_id=thread_id, plan=plan))
        except Exception as exc:  # relayed to the client, not a bare 500
            events.put(AgentStepEvent(type="error", message=str(exc), thread_id=thread_id))
        finally:
            events.put(_DONE)

    threading.Thread(target=worker, daemon=True).start()

    while True:
        event = await asyncio.to_thread(events.get)
        if event is _DONE:
            return
        yield event


async def _sse(request: TripRequest) -> AsyncIterator[str]:
    async for event in _stream_events(request):
        yield f"data: {event.model_dump_json()}\n\n"


@router.post("/trips")
async def plan_trip(request: TripRequest) -> StreamingResponse:
    return StreamingResponse(_sse(request), media_type="text/event-stream")


@router.get("/trips/{thread_id}")
async def get_trip(thread_id: str) -> TravelPlan:
    """Reconstructs a previously-generated plan for a shareable link.

    Reuses the LangGraph checkpointer's per-thread state rather than a
    separate store — every completed run is already saved there under its
    thread_id (in memory, or in Postgres if DATABASE_URL is set).
    """

    graph = get_travel_graph()
    snapshot = await asyncio.to_thread(graph.get_state, {"configurable": {"thread_id": thread_id}})
    state = snapshot.values
    query = state.get("query")

    if not query or "trip_summary" not in state:
        raise HTTPException(status_code=404, detail="Trip not found, or the run never completed.")

    return state_to_plan(state, query)


class _TargetPick(BaseModel):
    target: Literal["hotels", "itinerary"]


CLASSIFY_PROMPT = """Decide what part of an existing trip plan a follow-up request is
about. "hotels" for anything about where to stay (price, area, style, rating).
"itinerary" for everything else — activities, day-by-day changes, pacing, general
tweaks to the plan. When in doubt, pick "itinerary"."""


@router.post("/trips/{thread_id}/refine")
async def refine_trip(thread_id: str, body: RefineRequest) -> TravelPlan:
    """Re-runs only the part of the plan a follow-up request is actually about.

    A generic chatbot re-answer would re-read and regenerate everything; this
    reuses the checkpointed state and only touches hotels (if that's what
    changed) plus the itinerary/summary that depend on it — flights and
    weather, which the instruction can't meaningfully change, are left as-is.
    """

    graph = get_travel_graph()
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = await asyncio.to_thread(graph.get_state, config)
    state = dict(snapshot.values)
    query = state.get("query")

    if not query or "trip_summary" not in state:
        raise HTTPException(status_code=404, detail="Trip not found, or the run never completed.")

    classifier = get_llm(temperature=0).with_structured_output(_TargetPick)
    pick: _TargetPick = await asyncio.to_thread(
        retry_call,
        lambda: classifier.invoke(
            [SystemMessage(content=CLASSIFY_PROMPT), HumanMessage(content=body.instruction)]
        ),
    )  # type: ignore[assignment]

    if pick.target == "hotels":
        state["hotels"] = await asyncio.to_thread(search_hotels, query, body.instruction)
        state["refinement_instruction"] = None
    else:
        state["refinement_instruction"] = body.instruction

    itinerary_update = await asyncio.to_thread(itinerary_node, state)
    state.update(itinerary_update)
    state["refinement_instruction"] = None

    final_update = await asyncio.to_thread(final_node, state)
    state.update(final_update)

    await asyncio.to_thread(graph.update_state, config, state)
    return state_to_plan(state, query)
