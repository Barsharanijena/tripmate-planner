import { useCallback, useRef, useState } from 'react'
import { getTrip, refineTrip, streamTripPlan, type StepName, type TravelPlan } from '../lib/api'

export type PlannerPhase = 'idle' | 'loading' | 'success' | 'error'

export function useTripPlanner() {
  const [phase, setPhase] = useState<PlannerPhase>('idle')
  const [completedSteps, setCompletedSteps] = useState<Set<StepName>>(new Set())
  const [stepMessages, setStepMessages] = useState<Partial<Record<StepName, string>>>({})
  const [plan, setPlan] = useState<TravelPlan | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [threadId, setThreadId] = useState<string | undefined>(undefined)
  const [isRefining, setIsRefining] = useState(false)
  const [refineError, setRefineError] = useState<string | null>(null)

  const threadIdRef = useRef<string | undefined>(undefined)
  const lastMessageRef = useRef<string>('')
  const abortRef = useRef<AbortController | null>(null)

  const run = useCallback(async (message: string) => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    lastMessageRef.current = message
    setPhase('loading')
    setCompletedSteps(new Set())
    setStepMessages({})
    setPlan(null)
    setErrorMessage(null)

    setThreadId(undefined)

    try {
      for await (const event of streamTripPlan(message, undefined, controller.signal)) {
        if (event.thread_id) {
          threadIdRef.current = event.thread_id
          setThreadId(event.thread_id)
        }

        if (event.type === 'step' && event.step) {
          const step = event.step
          setCompletedSteps((prev) => {
            const next = new Set(prev)
            next.add(step)
            return next
          })
          if (event.message) {
            const label = event.message
            setStepMessages((prev) => ({ ...prev, [step]: label }))
          }
        } else if (event.type === 'result') {
          if (event.plan) {
            setPlan(event.plan)
            setPhase('success')
          } else {
            setErrorMessage('The planner finished without returning a trip plan. Please try again.')
            setPhase('error')
          }
        } else if (event.type === 'error') {
          setErrorMessage(event.message ?? 'Something went wrong while planning your trip.')
          setPhase('error')
        }
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return
      setErrorMessage(
        err instanceof Error
          ? err.message
          : 'Could not reach the trip planner. Check your connection and try again.',
      )
      setPhase('error')
    }
  }, [])

  const submit = useCallback(
    (message: string) => {
      const trimmed = message.trim()
      if (!trimmed) return
      void run(trimmed)
    },
    [run],
  )

  const retry = useCallback(() => {
    if (lastMessageRef.current) void run(lastMessageRef.current)
  }, [run])

  const reset = useCallback(() => {
    abortRef.current?.abort()
    threadIdRef.current = undefined
    lastMessageRef.current = ''
    setThreadId(undefined)
    setPhase('idle')
    setCompletedSteps(new Set())
    setStepMessages({})
    setPlan(null)
    setErrorMessage(null)
  }, [])

  /** Loads a previously-generated plan directly (shareable links), skipping the live-progress flow. */
  const loadThread = useCallback(async (id: string) => {
    abortRef.current?.abort()
    setPhase('loading')
    setCompletedSteps(new Set())
    setStepMessages({})
    setPlan(null)
    setErrorMessage(null)
    threadIdRef.current = id
    setThreadId(id)

    try {
      const loadedPlan = await getTrip(id)
      setPlan(loadedPlan)
      setPhase('success')
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Could not load this trip.')
      setPhase('error')
    }
  }, [])

  /** Applies a follow-up instruction to the current plan without regenerating everything. */
  const refine = useCallback(
    async (instruction: string) => {
      const trimmed = instruction.trim()
      if (!trimmed || !threadIdRef.current) return
      setIsRefining(true)
      setRefineError(null)
      try {
        const updated = await refineTrip(threadIdRef.current, trimmed)
        setPlan(updated)
      } catch (err) {
        setRefineError(err instanceof Error ? err.message : "Couldn't apply that change.")
      } finally {
        setIsRefining(false)
      }
    },
    [],
  )

  return {
    phase,
    completedSteps,
    stepMessages,
    plan,
    errorMessage,
    lastMessage: lastMessageRef.current,
    threadId,
    submit,
    retry,
    reset,
    loadThread,
    refine,
    isRefining,
    refineError,
  }
}
