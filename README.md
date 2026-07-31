# TripMate Planner

An AI trip planner: describe a trip in plain English and a small multi-agent
graph researches flights and hotels in parallel, drafts a day-by-day
itinerary, and hands back a structured plan that streams into the UI as it's
produced.

## Architecture

```
backend/   FastAPI + LangGraph service (Python)
frontend/  React + Vite + Tailwind app (TypeScript)
```

**Graph shape** (`backend/app/graph/build.py`): the user's message is parsed
into structured intent (`understand`), which fans out into two independent
branches — flight search and hotel research — that run concurrently, then
fan back in to a single itinerary-drafting step and a final summary step.

```
START -> understand -> flights   \
                     -> hotels    -> itinerary -> final -> END
```

Each node returns typed Pydantic models (`FlightOption`, `HotelOption`,
`ItineraryDay`, ...) instead of raw prose, so the frontend renders real UI
components (cards, timelines) rather than parsing markdown.

**Streaming**: `POST /api/trips` returns a Server-Sent Events stream — one
event per graph node as it completes, then a final `result` event with the
full `TravelPlan`. The frontend uses this to show live progress instead of a
blank loading spinner.

**Checkpointing**: trip threads persist to Postgres if `DATABASE_URL` is set,
otherwise they're kept in memory for the life of the process — no database is
required to run the app locally.

## Running locally

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in GEMINI_API_KEY at minimum
python -m uvicorn app.main:app --reload --port 8000
```

Required env vars (see `backend/.env.example`):

- `GEMINI_API_KEY` — powers query understanding, itinerary drafting, and the
  final summary via the Gemini API (Google AI Studio). Required. Get one at
  https://aistudio.google.com/apikey.
- `TAVILY_API_KEY` — hotel research. Optional; without it, hotel results are
  a clearly-labeled placeholder instead of a crash.
- `AVIATIONSTACK_API_KEY` — live flight data. Optional, same fallback
  behavior.
- `DATABASE_URL` — optional Postgres connection string for durable trip
  threads.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens on `http://localhost:5173` and talks to the backend at
`http://localhost:8000` (CORS is pre-configured for that origin). The UI
streams live per-agent progress (understanding → parallel flight/hotel
search → itinerary → final summary) rather than a blank loading state, and
supports light/dark mode.

## License

MIT — see `LICENSE`.
