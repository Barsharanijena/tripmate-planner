import type { ItineraryDay } from '../lib/api'

export function ItineraryTimeline({ days }: { days: ItineraryDay[] }) {
  return (
    <ol className="relative flex flex-col">
      {days.map((day, index) => {
        const isLast = index === days.length - 1
        return (
          <li key={day.day_number} className="relative flex gap-5 pb-9 last:pb-0">
            {!isLast && (
              <span
                aria-hidden="true"
                className="absolute left-[21px] top-11 -ml-px h-[calc(100%-2.75rem)] w-0.5 bg-stone-200 dark:bg-stone-800"
              />
            )}
            <span className="flex h-11 w-11 shrink-0 flex-col items-center justify-center rounded-full border border-clay-200 bg-clay-50 font-serif text-base font-medium text-clay-700 dark:border-clay-900/60 dark:bg-clay-950/40 dark:text-clay-400">
              {day.day_number}
            </span>
            <div className="min-w-0 flex-1 pt-2">
              <p className="font-serif text-lg font-medium tracking-tight text-stone-900 dark:text-stone-50">
                {day.title}
              </p>
              <ul className="mt-2.5 space-y-1.5">
                {day.activities.map((activity, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2.5 text-[14.5px] leading-relaxed text-stone-500 dark:text-stone-400"
                  >
                    <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-clay-300 dark:bg-clay-700" />
                    {activity}
                  </li>
                ))}
              </ul>
            </div>
          </li>
        )
      })}
    </ol>
  )
}
