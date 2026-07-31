import { useEffect, useRef } from 'react'
import { Compass, Moon, Sun } from 'lucide-react'
import { Composer } from './components/Composer'
import { ProgressTimeline } from './components/ProgressTimeline'
import { ResultsView } from './components/ResultsView'
import { ErrorState } from './components/ErrorState'
import { useTripPlanner } from './hooks/useTripPlanner'
import { useTheme } from './hooks/useTheme'

const TRIP_PATH = /^\/trip\/([^/]+)$/

function App() {
  const {
    phase,
    completedSteps,
    stepMessages,
    plan,
    errorMessage,
    lastMessage,
    threadId,
    submit,
    retry,
    reset,
    loadThread,
    refine,
    isRefining,
    refineError,
  } = useTripPlanner()
  const { theme, toggle: toggleTheme } = useTheme()

  // Deep-link support: /trip/:id loads a previously-generated plan directly.
  const loadedFromUrlRef = useRef(false)
  useEffect(() => {
    if (loadedFromUrlRef.current) return
    loadedFromUrlRef.current = true
    const match = TRIP_PATH.exec(window.location.pathname)
    if (match) void loadThread(match[1])
  }, [loadThread])

  // Keep the URL in sync so a completed plan is shareable/reloadable, and
  // "New trip" clears it — without pulling in a router for one route.
  useEffect(() => {
    if (phase === 'success' && threadId) {
      const target = `/trip/${threadId}`
      if (window.location.pathname !== target) window.history.pushState({}, '', target)
    }
  }, [phase, threadId])

  const handleReset = () => {
    reset()
    if (window.location.pathname !== '/') window.history.pushState({}, '', '/')
  }

  return (
    <div className="flex min-h-svh flex-col">
      <div className="h-[3px] w-full bg-clay-500" aria-hidden="true" />

      <header className="border-b border-stone-900/[0.06] dark:border-stone-100/[0.07]">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-5 py-5 sm:px-8">
          <button
            type="button"
            onClick={handleReset}
            className="group flex items-center gap-2"
            aria-label="TripMate — start a new trip"
          >
            <Compass
              className="h-5 w-5 text-clay-500 transition-transform duration-500 group-hover:rotate-45"
              strokeWidth={1.75}
            />
            <span className="font-serif text-[1.35rem] font-medium italic tracking-tight text-stone-900 dark:text-stone-50">
              Tripmate
            </span>
          </button>
          <div className="flex items-center gap-5">
            <span className="hidden text-[13px] tracking-wide text-stone-400 sm:inline dark:text-stone-500">
              Field notes from a crew of specialist planning agents
            </span>
            <button
              type="button"
              onClick={toggleTheme}
              aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-stone-900/[0.08] text-stone-500 transition-colors hover:border-clay-300 hover:text-clay-600 dark:border-stone-100/10 dark:text-stone-400 dark:hover:border-clay-800 dark:hover:text-clay-400"
            >
              {theme === 'dark' ? <Sun className="h-3.5 w-3.5" strokeWidth={1.9} /> : <Moon className="h-3.5 w-3.5" strokeWidth={1.9} />}
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1">
        {phase === 'idle' && <Composer onSubmit={submit} />}

        {phase === 'loading' && (
          <div className="mx-auto flex w-full max-w-6xl justify-center px-5 py-14 sm:px-8 sm:py-20">
            <ProgressTimeline
              completedSteps={completedSteps}
              stepMessages={stepMessages}
              requestSummary={lastMessage}
            />
          </div>
        )}

        {phase === 'error' && (
          <div className="mx-auto flex w-full max-w-6xl justify-center px-5 py-14 sm:px-8 sm:py-20">
            <ErrorState message={errorMessage ?? 'Something went wrong.'} onRetry={retry} onStartOver={handleReset} />
          </div>
        )}

        {phase === 'success' && plan && (
          <div className="mx-auto w-full max-w-6xl px-5 py-10 sm:px-8 sm:py-14">
            <ResultsView
              plan={plan}
              onNewTrip={handleReset}
              onRefine={refine}
              isRefining={isRefining}
              refineError={refineError}
            />
          </div>
        )}
      </main>

      <footer className="border-t border-stone-900/[0.06] py-6 dark:border-stone-100/[0.07]">
        <div className="mx-auto flex w-full max-w-6xl flex-col items-center gap-1 px-5 text-center sm:px-8">
          <p className="text-xs text-stone-400 dark:text-stone-500">
            Tripmate plans with live agents — flight and hotel details may vary from final bookings.
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App
