import { BedDouble, ExternalLink, Star } from 'lucide-react'
import type { HotelOption } from '../lib/api'

export function HotelCard({ hotel }: { hotel: HotelOption }) {
  return (
    <div className="group flex flex-col gap-3 rounded-2xl border border-stone-900/[0.07] bg-white p-4.5 transition-all duration-200 hover:-translate-y-0.5 hover:border-lagoon-200 hover:shadow-[0_16px_32px_-18px_rgba(20,80,75,0.24)] dark:border-stone-100/[0.08] dark:bg-stone-900 dark:hover:border-lagoon-900">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-lagoon-50 text-lagoon-600 dark:bg-lagoon-950/50 dark:text-lagoon-400">
            <BedDouble className="h-4 w-4" strokeWidth={1.9} />
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-stone-800 dark:text-stone-100">{hotel.name}</p>
            {hotel.area && <p className="text-xs text-stone-400 dark:text-stone-500">{hotel.area}</p>}
          </div>
        </div>
        {hotel.rating && (
          <span className="flex shrink-0 items-center gap-1 rounded-full border border-amber-200 bg-amber-50 px-2 py-1 text-xs font-medium text-amber-700 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-400">
            <Star className="h-3 w-3" fill="currentColor" strokeWidth={0} />
            {hotel.rating}
          </span>
        )}
      </div>

      <p className="text-sm leading-relaxed text-stone-500 dark:text-stone-400">{hotel.summary}</p>

      <div className="mt-auto flex items-center justify-between gap-3 pt-1">
        {hotel.price_estimate ? (
          <span className="font-serif text-base font-medium text-stone-900 dark:text-stone-50">
            {hotel.price_estimate}
          </span>
        ) : (
          <span />
        )}
        {hotel.source_url && (
          <a
            href={hotel.source_url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-xs font-medium text-lagoon-600 transition-colors hover:text-lagoon-700 dark:text-lagoon-400 dark:hover:text-lagoon-300"
          >
            View source
            <ExternalLink className="h-3 w-3" strokeWidth={2} />
          </a>
        )}
      </div>
    </div>
  )
}
