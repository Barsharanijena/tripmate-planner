import type { StepName } from './api'

export type StepGroup = {
  id: string
  steps: StepName[]
}

/**
 * The five backend steps, grouped by how they actually execute: `flights`
 * and `hotels` run concurrently on the backend, so they're modeled as one
 * parallel group rather than two sequential ones.
 */
export const STEP_GROUPS: StepGroup[] = [
  { id: 'understand', steps: ['understand'] },
  { id: 'search', steps: ['flights', 'hotels', 'weather'] },
  { id: 'itinerary', steps: ['itinerary'] },
  { id: 'final', steps: ['final'] },
]

export const STEP_COPY: Record<StepName, { title: string; description: string }> = {
  understand: {
    title: 'Understanding your trip',
    description: 'Reading your request for dates, destination, and budget',
  },
  flights: {
    title: 'Searching flights',
    description: 'Looking for flight options that fit your dates',
  },
  hotels: {
    title: 'Searching hotels',
    description: 'Finding places to stay at your destination',
  },
  weather: {
    title: 'Checking the weather',
    description: 'Pulling real conditions for your destination',
  },
  itinerary: {
    title: 'Building your itinerary',
    description: 'Planning a day-by-day schedule',
  },
  final: {
    title: 'Finalizing your plan',
    description: 'Pulling everything together into one trip plan',
  },
}

export type StepStatus = 'pending' | 'active' | 'done'

/** Derives a step's UI status from which steps have already completed. */
export function statusForStep(step: StepName, completed: ReadonlySet<StepName>): StepStatus {
  if (completed.has(step)) return 'done'
  const groupIndex = STEP_GROUPS.findIndex((group) => group.steps.includes(step))
  const priorGroupsDone = STEP_GROUPS.slice(0, groupIndex).every((group) =>
    group.steps.every((s) => completed.has(s)),
  )
  return priorGroupsDone ? 'active' : 'pending'
}

export function statusForGroup(group: StepGroup, completed: ReadonlySet<StepName>): StepStatus {
  const statuses = group.steps.map((step) => statusForStep(step, completed))
  if (statuses.every((s) => s === 'done')) return 'done'
  if (statuses.some((s) => s === 'active' || s === 'done')) return 'active'
  return 'pending'
}
