import { BedDouble, CalendarDays, Lightbulb, Plane, PlusCircle, SearchX } from 'lucide-react'
import type { TravelPlan } from '../lib/api'
import { FlightCard } from './FlightCard'
import { HotelCard } from './HotelCard'
import { ItineraryTimeline } from './ItineraryTimeline'

function SectionHeading({
  index,
  icon: Icon,
  title,
  count,
}: {
  index: string
  icon: typeof Plane
  title: string
  count?: number
}) {
  return (
    <div className="mb-5 flex items-end justify-between gap-4 border-b border-stone-900/[0.07] pb-3.5 dark:border-stone-100/[0.08]">
      <div className="flex items-baseline gap-3">
        <span className="font-serif text-sm text-clay-300 dark:text-clay-700" aria-hidden="true">
          {index}
        </span>
        <h3 className="flex items-center gap-2 font-serif text-xl font-medium tracking-tight text-stone-900 dark:text-stone-50">
          <Icon className="h-4 w-4 text-stone-400" strokeWidth={1.8} />
          {title}
        </h3>
      </div>
      {typeof count === 'number' && (
        <span className="text-xs text-stone-400 dark:text-stone-500">
          {count} {count === 1 ? 'option' : 'options'}
        </span>
      )}
    </div>
  )
}

function EmptySection({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center gap-2.5 rounded-2xl border border-stone-900/[0.07] bg-white/60 px-4 py-10 text-center dark:border-stone-100/[0.08] dark:bg-stone-900/40">
      <SearchX className="h-5 w-5 text-stone-300 dark:text-stone-700" strokeWidth={1.6} />
      <p className="text-sm text-stone-400 dark:text-stone-500">{message}</p>
    </div>
  )
}

type ResultsViewProps = {
  plan: TravelPlan
  onNewTrip: () => void
}

export function ResultsView({ plan, onNewTrip }: ResultsViewProps) {
  return (
    <div className="w-full animate-fade-up">
      <div className="mb-12 grid grid-cols-1 gap-8 lg:grid-cols-[1fr_auto] lg:items-start lg:gap-14">
        <div>
          <div className="mb-4 flex items-center justify-between gap-4">
            {plan.origin ? (
              <p className="text-[13px] tracking-wide text-stone-400 dark:text-stone-500">
                {plan.origin} <span className="text-clay-400">&rarr;</span> {plan.destination}
              </p>
            ) : (
              <span />
            )}
            <button
              type="button"
              onClick={onNewTrip}
              className="inline-flex shrink-0 items-center gap-1.5 text-sm font-medium text-stone-500 transition-colors hover:text-clay-600 dark:text-stone-400 dark:hover:text-clay-400"
            >
              <PlusCircle className="h-4 w-4" strokeWidth={1.9} />
              New trip
            </button>
          </div>

          <h1 className="text-balance font-serif text-4xl font-medium tracking-tight text-stone-900 sm:text-5xl dark:text-stone-50">
            {plan.destination}
          </h1>

          <p className="mt-4 max-w-2xl text-balance text-[15.5px] leading-relaxed text-stone-500 dark:text-stone-400">
            {plan.trip_summary}
          </p>
        </div>

        {plan.budget_estimate && (
          <div className="flex shrink-0 flex-col justify-center rounded-2xl border border-clay-200/70 bg-gradient-to-br from-clay-50 to-sand-100 px-6 py-5 dark:border-clay-900/50 dark:from-clay-950/30 dark:to-stone-900">
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-clay-600 dark:text-clay-400">
              Estimated budget
            </p>
            <p className="mt-1.5 whitespace-nowrap font-serif text-2xl font-medium text-stone-900 dark:text-stone-50">
              {plan.budget_estimate}
            </p>
          </div>
        )}
      </div>

      <section className="mb-10">
        <SectionHeading index="01" icon={Plane} title="Flights" count={plan.flights.length} />
        {plan.flights.length > 0 ? (
          <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2">
            {plan.flights.map((flight, i) => (
              <FlightCard key={i} flight={flight} />
            ))}
          </div>
        ) : (
          <EmptySection message="No flight options were found for this trip." />
        )}
      </section>

      <section className="mb-10">
        <SectionHeading index="02" icon={BedDouble} title="Hotels" count={plan.hotels.length} />
        {plan.hotels.length > 0 ? (
          <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2">
            {plan.hotels.map((hotel, i) => (
              <HotelCard key={i} hotel={hotel} />
            ))}
          </div>
        ) : (
          <EmptySection message="No hotel options were found for this trip." />
        )}
      </section>

      <section className="mb-10">
        <SectionHeading index="03" icon={CalendarDays} title="Itinerary" />
        {plan.itinerary.length > 0 ? (
          <div className="rounded-2xl border border-stone-900/[0.07] bg-white p-6 sm:p-7 dark:border-stone-100/[0.08] dark:bg-stone-900">
            <ItineraryTimeline days={plan.itinerary} />
          </div>
        ) : (
          <EmptySection message="No itinerary was generated for this trip." />
        )}
      </section>

      {plan.recommendations.length > 0 && (
        <section>
          <SectionHeading index="04" icon={Lightbulb} title="Good to know" />
          <ul className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
            {plan.recommendations.map((rec, i) => (
              <li
                key={i}
                className="flex items-start gap-2.5 rounded-2xl border border-lagoon-100 bg-lagoon-50/40 px-4 py-3.5 text-[13.5px] leading-relaxed text-stone-600 dark:border-lagoon-900/40 dark:bg-lagoon-950/20 dark:text-stone-300"
              >
                <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-lagoon-500 dark:text-lagoon-400" strokeWidth={1.8} />
                {rec}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}
