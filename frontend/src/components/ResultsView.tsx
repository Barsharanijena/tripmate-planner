import { useState } from 'react'
import {
  BedDouble,
  CalendarDays,
  Check,
  CloudSun,
  Lightbulb,
  Link2,
  Luggage,
  Plane,
  Printer,
  PlusCircle,
  SearchX,
  Wallet,
} from 'lucide-react'
import type { BudgetLine, TravelPlan } from '../lib/api'
import { FlightCard } from './FlightCard'
import { HotelCard } from './HotelCard'
import { ItineraryTimeline } from './ItineraryTimeline'

function ShareButton() {
  const [copied, setCopied] = useState(false)

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Clipboard permission denied or unavailable — the URL is already
      // shareable via the address bar, so this is a soft failure.
    }
  }

  return (
    <button
      type="button"
      onClick={handleShare}
      className="inline-flex shrink-0 items-center gap-1.5 text-sm font-medium text-stone-500 transition-colors hover:text-clay-600 dark:text-stone-400 dark:hover:text-clay-400"
    >
      {copied ? (
        <>
          <Check className="h-4 w-4 text-lagoon-500" strokeWidth={2} />
          Link copied
        </>
      ) : (
        <>
          <Link2 className="h-4 w-4" strokeWidth={1.9} />
          Share
        </>
      )}
    </button>
  )
}

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

const CATEGORY_LABEL: Record<BudgetLine['category'], string> = {
  flights: 'Flights',
  hotels: 'Hotels',
  food: 'Food',
  activities: 'Activities',
  other: 'Other',
}

function formatAmount(n: number): string {
  return n >= 1000 ? n.toLocaleString(undefined, { maximumFractionDigits: 0 }) : n.toFixed(0)
}

function formatRange(line: BudgetLine): string {
  const { amount_low, amount_high, currency } = line
  if (amount_low == null && amount_high == null) return 'Not estimable'
  if (amount_low != null && amount_high != null && amount_low !== amount_high) {
    return `${currency} ${formatAmount(amount_low)}–${formatAmount(amount_high)}`
  }
  return `${currency} ${formatAmount((amount_low ?? amount_high) as number)}`
}

function totalRange(budget: BudgetLine[]): string | null {
  if (budget.length === 0) return null
  const currency = budget[0].currency
  const low = budget.reduce((sum, l) => sum + (l.amount_low ?? l.amount_high ?? 0), 0)
  const high = budget.reduce((sum, l) => sum + (l.amount_high ?? l.amount_low ?? 0), 0)
  return `${currency} ${formatAmount(low)}–${formatAmount(high)}`
}

function EmptySection({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center gap-2.5 rounded-2xl border border-stone-900/[0.07] bg-white/60 px-4 py-10 text-center dark:border-stone-100/[0.08] dark:bg-stone-900/40">
      <SearchX className="h-5 w-5 text-stone-300 dark:text-stone-700" strokeWidth={1.6} />
      <p className="text-sm text-stone-400 dark:text-stone-500">{message}</p>
    </div>
  )
}

function RefineComposer({
  onRefine,
  isRefining,
  refineError,
}: {
  onRefine: (instruction: string) => void
  isRefining: boolean
  refineError: string | null
}) {
  const [value, setValue] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!value.trim() || isRefining) return
    onRefine(value)
    setValue('')
  }

  return (
    <section className="mt-4 print:hidden">
      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-3 rounded-2xl border border-stone-900/[0.07] bg-white p-4 sm:flex-row sm:items-center dark:border-stone-100/[0.08] dark:bg-stone-900"
      >
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={isRefining}
          placeholder="Tweak this plan — e.g. “cheaper hotels” or “make day 2 more relaxed”"
          className="flex-1 bg-transparent text-sm text-stone-700 placeholder:text-stone-400 focus:outline-none disabled:opacity-60 dark:text-stone-200 dark:placeholder:text-stone-500"
        />
        <button
          type="submit"
          disabled={isRefining || !value.trim()}
          className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-full bg-clay-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-clay-600 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isRefining ? 'Applying…' : 'Refine'}
        </button>
      </form>
      {refineError && <p className="mt-2 text-xs text-red-500 dark:text-red-400">{refineError}</p>}
    </section>
  )
}

type ResultsViewProps = {
  plan: TravelPlan
  onNewTrip: () => void
  onRefine: (instruction: string) => void
  isRefining: boolean
  refineError: string | null
}

export function ResultsView({ plan, onNewTrip, onRefine, isRefining, refineError }: ResultsViewProps) {
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
            <div className="flex items-center gap-5 print:hidden">
              <ShareButton />
              <button
                type="button"
                onClick={() => window.print()}
                className="inline-flex shrink-0 items-center gap-1.5 text-sm font-medium text-stone-500 transition-colors hover:text-clay-600 dark:text-stone-400 dark:hover:text-clay-400"
              >
                <Printer className="h-4 w-4" strokeWidth={1.9} />
                Print / PDF
              </button>
              <button
                type="button"
                onClick={onNewTrip}
                className="inline-flex shrink-0 items-center gap-1.5 text-sm font-medium text-stone-500 transition-colors hover:text-clay-600 dark:text-stone-400 dark:hover:text-clay-400"
              >
                <PlusCircle className="h-4 w-4" strokeWidth={1.9} />
                New trip
              </button>
            </div>
          </div>

          <h1 className="text-balance font-serif text-4xl font-medium tracking-tight text-stone-900 sm:text-5xl dark:text-stone-50">
            {plan.destination}
          </h1>

          <p className="mt-4 max-w-2xl text-balance text-[15.5px] leading-relaxed text-stone-500 dark:text-stone-400">
            {plan.trip_summary}
          </p>
        </div>

        <div className="flex shrink-0 flex-col gap-3 sm:flex-row lg:flex-col">
          {plan.weather && (
            <div className="flex flex-col justify-center rounded-2xl border border-lagoon-200/70 bg-lagoon-50/50 px-6 py-4 dark:border-lagoon-900/50 dark:bg-lagoon-950/20">
              <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-lagoon-600 dark:text-lagoon-400">
                <CloudSun className="h-3.5 w-3.5" strokeWidth={2} />
                {plan.weather.period_label}
              </p>
              <p className="mt-1 whitespace-nowrap font-serif text-lg font-medium text-stone-900 dark:text-stone-50">
                {plan.weather.condition_summary}
              </p>
              {plan.weather.avg_high_c != null && (
                <p className="mt-0.5 text-xs text-stone-400 dark:text-stone-500">
                  {plan.weather.avg_high_c}°C / {plan.weather.avg_low_c}°C avg
                </p>
              )}
            </div>
          )}
          {totalRange(plan.budget) && (
            <div className="flex flex-col justify-center rounded-2xl border border-clay-200/70 bg-gradient-to-br from-clay-50 to-sand-100 px-6 py-5 dark:border-clay-900/50 dark:from-clay-950/30 dark:to-stone-900">
              <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-clay-600 dark:text-clay-400">
                Estimated budget
              </p>
              <p className="mt-1.5 whitespace-nowrap font-serif text-2xl font-medium text-stone-900 dark:text-stone-50">
                {totalRange(plan.budget)}
              </p>
            </div>
          )}
        </div>
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

      {plan.budget.length > 0 && (
        <section className="mb-10">
          <SectionHeading index="04" icon={Wallet} title="Budget breakdown" />
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {plan.budget.map((line, i) => (
              <div
                key={i}
                className="rounded-2xl border border-stone-900/[0.07] bg-white px-5 py-4 dark:border-stone-100/[0.08] dark:bg-stone-900"
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium text-stone-800 dark:text-stone-100">
                    {CATEGORY_LABEL[line.category]}
                  </p>
                  <span
                    className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
                      line.basis === 'sourced'
                        ? 'bg-lagoon-100 text-lagoon-700 dark:bg-lagoon-950/50 dark:text-lagoon-300'
                        : 'bg-stone-100 text-stone-500 dark:bg-stone-800 dark:text-stone-400'
                    }`}
                  >
                    {line.basis}
                  </span>
                </div>
                <p className="mt-1 font-serif text-lg text-stone-900 dark:text-stone-50">{formatRange(line)}</p>
                {line.note && <p className="mt-1 text-xs leading-relaxed text-stone-400 dark:text-stone-500">{line.note}</p>}
              </div>
            ))}
          </div>
        </section>
      )}

      {plan.packing_tips.length > 0 && (
        <section className="mb-10">
          <SectionHeading index="05" icon={Luggage} title="Pack for the weather" />
          <ul className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
            {plan.packing_tips.map((tip, i) => (
              <li
                key={i}
                className="flex items-start gap-2.5 rounded-2xl border border-clay-100 bg-clay-50/40 px-4 py-3.5 text-[13.5px] leading-relaxed text-stone-600 dark:border-clay-900/40 dark:bg-clay-950/20 dark:text-stone-300"
              >
                <Luggage className="mt-0.5 h-4 w-4 shrink-0 text-clay-500 dark:text-clay-400" strokeWidth={1.8} />
                {tip}
              </li>
            ))}
          </ul>
        </section>
      )}

      {plan.recommendations.length > 0 && (
        <section>
          <SectionHeading index="06" icon={Lightbulb} title="Good to know" />
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

      <RefineComposer onRefine={onRefine} isRefining={isRefining} refineError={refineError} />
    </div>
  )
}
