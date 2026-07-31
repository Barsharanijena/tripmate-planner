import asyncio
import queue
import threading
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.graph.build import get_travel_graph, new_thread_id, state_to_plan
from app.schemas import AgentStepEvent, TripRequest

router = APIRouter()

STEP_MESSAGES = {
    "understand": "Reading your request",
    "flights": "Searching flights",
    "hotels": "Researching hotels",
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
