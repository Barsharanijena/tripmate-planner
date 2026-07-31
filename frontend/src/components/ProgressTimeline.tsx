import clsx from 'clsx'
import { BedDouble, CalendarDays, Check, CloudSun, Plane, Search, Sparkles, type LucideIcon } from 'lucide-react'
import { STEP_COPY, STEP_GROUPS, statusForGroup, statusForStep, type StepStatus } from '../lib/steps'
import type { StepName } from '../lib/api'

type ProgressTimelineProps = {
  completedSteps: ReadonlySet<StepName>
  stepMessages: Partial<Record<StepName, string>>
  requestSummary: string
}

const STEP_ICONS: Record<StepName, LucideIcon> = {
  understand: Search,
  flights: Plane,
  hotels: BedDouble,
  weather: CloudSun,
  itinerary: CalendarDays,
  final: Sparkles,
}

function StatusDot({ step, status, size = 'md' }: { step: StepName; status: StepStatus; size?: 'md' | 'sm' }) {
  const Icon = STEP_ICONS[step]
  const dims = size === 'md' ? 'h-11 w-11' : 'h-8 w-8'
  const iconDims = size === 'md' ? 'h-4.5 w-4.5' : 'h-3.5 w-3.5'

  return (
    <span
      className={clsx(
        'relative flex shrink-0 items-center justify-center rounded-full border transition-all duration-500',
        dims,
        status === 'done' && 'animate-pop border-clay-500 bg-clay-500 text-white shadow-[0_6px_16px_-6px_rgba(211,95,52,0.6)]',
        status === 'active' &&
          'animate-soft-pulse border-clay-300 bg-white text-clay-500 dark:border-clay-800 dark:bg-stone-900',
        status === 'pending' &&
          'border-stone-200 bg-white text-stone-300 dark:border-stone-800 dark:bg-stone-900 dark:text-stone-700',
      )}
    >
      {status === 'done' ? (
        <Check className={iconDims} strokeWidth={2.75} />
      ) : (
        <Icon className={clsx(iconDims, status === 'active' && 'animate-pulse')} strokeWidth={1.9} />
      )}
    </span>
  )
}

function SkeletonLine({ visible }: { visible: boolean }) {
  if (!visible) return null
  return <span className="skeleton-shimmer animate-shimmer mt-2 block h-2.5 w-4/5 rounded-full" />
}

function ParallelCard({ step, status, message }: { step: StepName; status: StepStatus; message?: string }) {
  const copy = STEP_COPY[step]
  return (
    <div
      className={clsx(
        'flex items-start gap-3 rounded-2xl border px-4 py-3.5 transition-all duration-300',
        status === 'done' &&
          'border-clay-200 bg-clay-50/50 dark:border-clay-900/60 dark:bg-clay-950/20',
        status === 'active' && 'border-clay-300 bg-white shadow-sm dark:border-clay-800 dark:bg-stone-900',
        status === 'pending' && 'border-stone-200 bg-white/50 dark:border-stone-800 dark:bg-stone-900/40',
      )}
    >
      <StatusDot step={step} status={status} size="sm" />
      <div className="min-w-0 flex-1 pt-0.5">
        <p
          className={clsx(
            'text-[13.5px] font-medium transition-colors',
            status === 'pending' ? 'text-stone-400 dark:text-stone-600' : 'text-stone-800 dark:text-stone-100',
          )}
        >
          {copy.title}
        </p>
        {status === 'active' && !message ? (
          <SkeletonLine visible />
        ) : (
          <p className="animate-fade-in mt-1 text-xs leading-relaxed text-stone-400 dark:text-stone-500">
            {message ?? copy.description}
          </p>
        )}
      </div>
    </div>
  )
}

export function ProgressTimeline({ completedSteps, stepMessages, requestSummary }: ProgressTimelineProps) {
  return (
    <div className="w-full max-w-xl">
      <div className="mb-10 animate-fade-up">
        <div className="mb-3 flex items-center gap-2.5 text-clay-600 dark:text-clay-400">
          <span className="h-px w-8 bg-current" />
          <span className="text-[11px] font-semibold uppercase tracking-[0.18em]">At work</span>
        </div>
        <h2 className="font-serif text-3xl font-medium tracking-tight text-stone-900 dark:text-stone-50">
          Planning your trip
        </h2>
        <p className="mt-2.5 text-[15px] italic leading-relaxed text-stone-400 dark:text-stone-500">
          &ldquo;{requestSummary}&rdquo;
        </p>
      </div>

      <ol className="relative flex flex-col">
        {STEP_GROUPS.map((group, index) => {
          const groupStatus = statusForGroup(group, completedSteps)
          const isLast = index === STEP_GROUPS.length - 1
          const single = group.steps.length === 1

          return (
            <li
              key={group.id}
              className="relative flex animate-fade-up gap-4 pb-9 last:pb-0"
              style={{ animationDelay: `${index * 90}ms` }}
            >
              {!isLast && (
                <span
                  aria-hidden="true"
                  className="absolute left-[22px] top-11 -ml-px h-[calc(100%-2.75rem)] w-0.5 overflow-hidden bg-stone-200 dark:bg-stone-800"
                >
                  <span
                    className={clsx(
                      'block h-full w-full origin-top bg-clay-400 transition-transform duration-700 ease-out dark:bg-clay-600',
                      groupStatus === 'done' ? 'scale-y-100' : 'scale-y-0',
                    )}
                  />
                </span>
              )}

              <StatusDot step={group.steps[0]} status={groupStatus} />

              <div className="min-w-0 flex-1 pt-2">
                {single ? (
                  <div>
                    <p
                      className={clsx(
                        'text-[15px] font-medium transition-colors',
                        groupStatus === 'pending'
                          ? 'text-stone-400 dark:text-stone-600'
                          : 'text-stone-800 dark:text-stone-100',
                      )}
                    >
                      {STEP_COPY[group.steps[0]].title}
                    </p>
                    {groupStatus === 'active' && !stepMessages[group.steps[0]] ? (
                      <SkeletonLine visible />
                    ) : (
                      <p className="animate-fade-in mt-1 text-[13.5px] text-stone-400 dark:text-stone-500">
                        {stepMessages[group.steps[0]] ?? STEP_COPY[group.steps[0]].description}
                      </p>
                    )}
                  </div>
                ) : (
                  <div>
                    <p className="mb-2.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-stone-400 dark:text-stone-600">
                      Running in parallel
                    </p>
                    <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                      {group.steps.map((step) => (
                        <ParallelCard
                          key={step}
                          step={step}
                          status={statusForStep(step, completedSteps)}
                          message={stepMessages[step]}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </li>
          )
        })}
      </ol>
    </div>
  )
}
