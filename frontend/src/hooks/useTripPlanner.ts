import { useCallback, useRef, useState } from 'react'
import { streamTripPlan, type StepName, type TravelPlan } from '../lib/api'

export type PlannerPhase = 'idle' | 'loading' | 'success' | 'error'

export function useTripPlanner() {
  const [phase, setPhase] = useState<PlannerPhase>('idle')
  const [completedSteps, setCompletedSteps] = useState<Set<StepName>>(new Set())
  const [stepMessages, setStepMessages] = useState<Partial<Record<StepName, string>>>({})
  const [plan, setPlan] = useState<TravelPlan | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

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

    try {
      for await (const event of streamTripPlan(message, undefined, controller.signal)) {
        if (event.thread_id) threadIdRef.current = event.thread_id

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
    setPhase('idle')
    setCompletedSteps(new Set())
    setStepMessages({})
    setPlan(null)
    setErrorMessage(null)
  }, [])

  return {
    phase,
    completedSteps,
    stepMessages,
    plan,
    errorMessage,
    lastMessage: lastMessageRef.current,
    submit,
    retry,
    reset,
  }
}
