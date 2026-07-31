from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.observability import configure_langsmith

configure_langsmith()  # must run before the graph/LLM clients below are ever constructed

from app.routes.travel import router as travel_router  # noqa: E402

app = FastAPI(
    title="TripMate Planner API",
    description="Multi-agent trip planner: parallel flight/hotel research feeding a structured itinerary graph.",
    version="0.1.0",
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(travel_router, prefix="/api")


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}
