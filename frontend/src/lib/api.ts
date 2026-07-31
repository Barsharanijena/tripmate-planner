// Base URL for the TripMate FastAPI backend. Set VITE_API_BASE_URL at build
// time for a deployed backend; defaults to local dev otherwise.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export type StepName = 'understand' | 'flights' | 'hotels' | 'weather' | 'itinerary' | 'final'

export type FlightOption = {
  airline: string
  flight_number?: string | null
  origin_iata?: string | null
  destination_iata?: string | null
  departure_time?: string | null
  arrival_time?: string | null
  status?: string | null
  price?: number | null
  currency?: string | null
  /** When present, often an explanatory/error message (e.g. missing API key, no live matches). */
  notes?: string | null
}

export type HotelOption = {
  name: string
  area?: string | null
  price_estimate?: string | null
  price_per_night_low?: number | null
  price_per_night_high?: number | null
  currency?: string | null
  rating?: string | null
  summary: string
  source_url?: string | null
}

export type ItineraryDay = {
  day_number: number
  title: string
  activities: string[]
}

export type WeatherSummary = {
  basis: 'forecast' | 'historical_average'
  period_label: string
  avg_high_c?: number | null
  avg_low_c?: number | null
  precipitation_chance_pct?: number | null
  condition_summary: string
}

export type BudgetLine = {
  category: 'flights' | 'hotels' | 'food' | 'activities' | 'other'
  amount_low?: number | null
  amount_high?: number | null
  currency: string
  basis: 'sourced' | 'estimated'
  note?: string | null
}

export type TravelPlan = {
  destination: string
  origin?: string | null
  trip_summary: string
  flights: FlightOption[]
  hotels: HotelOption[]
  weather?: WeatherSummary | null
  itinerary: ItineraryDay[]
  budget: BudgetLine[]
  packing_tips: string[]
  recommendations: string[]
}

export type AgentStepEvent = {
  type: 'step' | 'result' | 'error'
  step?: StepName
  status?: 'started' | 'completed' | 'failed'
  message?: string
  thread_id?: string
  plan?: TravelPlan
}

/**
 * POSTs a trip request to the backend and yields each parsed SSE event as it
 * arrives. Uses fetch + a streaming reader (not EventSource, since this is a
 * POST with a JSON body). Buffers across chunk boundaries because a single
 * `data: {...}\n\n` event can be split across multiple reads.
 */
export async function* streamTripPlan(
  message: string,
  threadId: string | undefined,
  signal?: AbortSignal,
): AsyncGenerator<AgentStepEvent> {
  const response = await fetch(`${API_BASE_URL}/api/trips`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(threadId ? { message, thread_id: threadId } : { message }),
    signal,
  })

  if (!response.ok || !response.body) {
    throw new Error(`The planner couldn't be reached (status ${response.status}).`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  const parseEvent = (rawEvent: string): AgentStepEvent | null => {
    for (const line of rawEvent.split('\n')) {
      if (!line.startsWith('data: ')) continue
      const jsonText = line.slice('data: '.length).trim()
      if (!jsonText) continue
      try {
        return JSON.parse(jsonText) as AgentStepEvent
      } catch {
        return null
      }
    }
    return null
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const events = buffer.split('\n\n')
    buffer = events.pop() ?? ''

    for (const rawEvent of events) {
      const parsed = parseEvent(rawEvent)
      if (parsed) yield parsed
    }
  }

  // Flush a trailing event that wasn't followed by a final \n\n.
  if (buffer.trim()) {
    const parsed = parseEvent(buffer)
    if (parsed) yield parsed
  }
}

/**
 * Applies a follow-up instruction to an existing plan ("cheaper hotels",
 * "make day 2 more relaxed"). The backend re-runs only the affected part —
 * this returns the updated plan directly, not a stream, since a refine only
 * touches one or two agents and is fast enough not to need live progress.
 */
export async function refineTrip(threadId: string, instruction: string): Promise<TravelPlan> {
  const response = await fetch(`${API_BASE_URL}/api/trips/${encodeURIComponent(threadId)}/refine`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ instruction }),
  })
  if (!response.ok) {
    throw new Error(`Couldn't apply that change (status ${response.status}).`)
  }
  return response.json()
}

/** Fetches a previously-generated plan by its thread id, for shareable links. */
export async function getTrip(threadId: string): Promise<TravelPlan> {
  const response = await fetch(`${API_BASE_URL}/api/trips/${encodeURIComponent(threadId)}`)
  if (!response.ok) {
    throw new Error(
      response.status === 404
        ? "This trip link doesn't exist or has expired."
        : `The planner couldn't be reached (status ${response.status}).`,
    )
  }
  return response.json()
}
