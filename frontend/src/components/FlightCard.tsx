import { Plane, TriangleAlert } from 'lucide-react'
import type { FlightOption } from '../lib/api'

export function FlightCard({ flight }: { flight: FlightOption }) {
  const hasRoute = flight.origin_iata || flight.destination_iata
  const hasTimes = flight.departure_time || flight.arrival_time

  return (
    <div className="group flex flex-col gap-3.5 rounded-2xl border border-stone-900/[0.07] bg-white p-4.5 transition-all duration-200 hover:-translate-y-0.5 hover:border-clay-200 hover:shadow-[0_16px_32px_-18px_rgba(120,60,20,0.28)] dark:border-stone-100/[0.08] dark:bg-stone-900 dark:hover:border-clay-900">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-clay-50 text-clay-600 dark:bg-clay-950/50 dark:text-clay-400">
            <Plane className="h-4 w-4" strokeWidth={1.9} />
          </span>
          <div>
            <p className="text-sm font-medium text-stone-800 dark:text-stone-100">{flight.airline}</p>
            {flight.flight_number && (
              <p className="text-xs text-stone-400 dark:text-stone-500">{flight.flight_number}</p>
            )}
          </div>
        </div>
        {flight.status && (
          <span className="shrink-0 rounded-full border border-stone-200 bg-stone-50 px-2.5 py-1 text-xs font-medium text-stone-500 dark:border-stone-700 dark:bg-stone-800 dark:text-stone-400">
            {flight.status}
          </span>
        )}
      </div>

      {hasRoute && (
        <div className="flex items-center gap-3">
          <div className="min-w-0 flex-1">
            <p className="font-serif text-xl font-medium text-stone-900 dark:text-stone-50">
              {flight.origin_iata ?? '—'}
            </p>
            {flight.departure_time && (
              <p className="mt-0.5 text-xs text-stone-400 dark:text-stone-500">
                Departs {flight.departure_time}
              </p>
            )}
          </div>
          <div className="flex flex-1 items-center gap-1.5 text-stone-300 dark:text-stone-700">
            <span className="h-px flex-1 bg-current" />
            <Plane className="h-3.5 w-3.5 rotate-90 sm:rotate-0" strokeWidth={1.8} />
            <span className="h-px flex-1 bg-current" />
          </div>
          <div className="min-w-0 flex-1 text-right">
            <p className="font-serif text-xl font-medium text-stone-900 dark:text-stone-50">
              {flight.destination_iata ?? '—'}
            </p>
            {flight.arrival_time && (
              <p className="mt-0.5 text-xs text-stone-400 dark:text-stone-500">
                Arrives {flight.arrival_time}
              </p>
            )}
          </div>
        </div>
      )}

      {!hasRoute && hasTimes && (
        <div className="flex justify-between text-xs text-stone-400 dark:text-stone-500">
          {flight.departure_time && <span>Departs {flight.departure_time}</span>}
          {flight.arrival_time && <span>Arrives {flight.arrival_time}</span>}
        </div>
      )}

      {flight.notes && (
        <p className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-relaxed text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-300">
          <TriangleAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" strokeWidth={2} />
          {flight.notes}
        </p>
      )}
    </div>
  )
}
