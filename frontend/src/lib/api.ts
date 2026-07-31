// Base URL for the TripMate FastAPI backend. Hardcoded for v1 — no env plumbing needed.
export const API_BASE_URL = 'http://localhost:8000'

export type StepName = 'understand' | 'flights' | 'hotels' | 'itinerary' | 'final'

export type FlightOption = {
  airline: string
  flight_number?: string | null
  origin_iata?: string | null
  destination_iata?: string | null
  departure_time?: string | null
  arrival_time?: string | null
  status?: string | null
  /** When present, often an explanatory/error message (e.g. missing API key, no live matches). */
  notes?: string | null
}

export type HotelOption = {
  name: string
  area?: string | null
  price_estimate?: string | null
  rating?: string | null
  summary: string
  source_url?: string | null
}

export type ItineraryDay = {
  day_number: number
  title: string
  activities: string[]
}

export type TravelPlan = {
  destination: string
  origin?: string | null
  trip_summary: string
  flights: FlightOption[]
  hotels: HotelOption[]
  itinerary: ItineraryDay[]
  budget_estimate?: string | null
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
