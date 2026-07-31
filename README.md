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
into structured intent (`understand`), which fans out into three independent
branches — flights, hotels, and weather — that run concurrently, then fan
back in to a single itinerary-drafting step and a final summary step.

```
START -> understand -> flights   \
                     -> hotels    -> itinerary -> final -> END
                     -> weather  /
```

Each node returns typed Pydantic models (`FlightOption`, `HotelOption`,
`WeatherSummary`, `ItineraryDay`, `BudgetLine`, ...) instead of raw prose, so
the frontend renders real UI components (cards, timelines, a budget table)
rather than parsing markdown.

**Real data over LLM guesses, wherever possible:**
- Flights: real bookable fares via Amadeus if configured, else AviationStack
  live-status data (with an honest "no fares available" note, not an
  invented price).
- Hotels: sourced from live web search (Tavily, `search_depth="advanced"`),
  with numeric nightly prices extracted from the actual source text.
- Weather: real Open-Meteo data — a live 7-day forecast, or actual historical
  daily data for the stated month if given (not "it's probably cold in
  December" from pretrained knowledge).
- Budget breakdown: hotels/flights lines are computed by summing the real
  sourced prices above (labeled `basis: "sourced"`); only food/activities
  (which have no real price source yet) are LLM-estimated
  (`basis: "estimated"`) — both are shown, honestly labeled, in the UI.
- Airports: place names resolve to real airports via an alias table, then
  word-boundary matching, then (for small towns/regions with no airport of
  their own) the genuinely nearest real airport by geocoded distance — never
  a spelling-similarity guess, which can confidently land on an unrelated
  place.

**Streaming**: `POST /api/trips` returns a Server-Sent Events stream — one
event per graph node as it completes, then a final `result` event with the
full `TravelPlan`. The frontend uses this to show live progress instead of a
blank loading spinner.

**Refining a plan**: `POST /api/trips/{thread_id}/refine` with
`{"instruction": "cheaper hotels"}` re-runs only the affected part (hotels,
or the itinerary/summary) using the checkpointed state, rather than
regenerating the whole trip — flights and weather are left untouched.

**Sharing a plan**: every generated plan is reachable at `/trip/{thread_id}`
(`GET /api/trips/{thread_id}`), reusing the LangGraph checkpointer's
per-thread state as the store rather than a separate database. The frontend
has a Share button (copies the URL) and a Print/PDF button.

**Checkpointing**: trip threads persist to Postgres if `DATABASE_URL` is set,
otherwise they're kept in memory for the life of the process — no database is
required to run the app locally (shareable links just won't survive a
restart in that case).

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
- `AMADEUS_API_KEY` / `AMADEUS_API_SECRET` — optional, free at
  developers.amadeus.com. When both are set, real bookable fares are used
  instead of AviationStack's status-only data.
- `DATABASE_URL` — optional Postgres connection string for durable trip
  threads.
- `LANGSMITH_API_KEY` / `LANGSMITH_PROJECT` — optional. When set, every graph
  run is traced to LangSmith (smith.langchain.com): per-node inputs/outputs,
  token usage, and latency for each of the 5 agents. Free tier available.

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
