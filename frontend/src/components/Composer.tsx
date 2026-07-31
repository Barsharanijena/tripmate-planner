import { useState, type FormEvent, type KeyboardEvent } from 'react'
import { ArrowRight, ArrowUpRight, Map, Search, Sparkles } from 'lucide-react'

const EXAMPLE_PROMPTS = [
  'Plan a 5 day trip to Tokyo under $1500',
  'Weekend in Lisbon for two, mid-range budget',
  '10 days backpacking Peru, focus on hiking',
  'Romantic anniversary trip to Kyoto in the fall',
]

const HOW_IT_WORKS = [
  {
    n: '01',
    icon: Search,
    title: 'Understands the brief',
    detail: 'Pulls dates, destination, party size, and budget out of what you type.',
  },
  {
    n: '02',
    icon: Map,
    title: 'Works the routes',
    detail: 'Flight and hotel agents search in parallel, live.',
  },
  {
    n: '03',
    icon: Sparkles,
    title: 'Drafts the plan',
    detail: 'Assembles a day-by-day itinerary and hands you the full trip.',
  },
]

type ComposerProps = {
  onSubmit: (message: string) => void
  disabled?: boolean
}

export function Composer({ onSubmit, disabled = false }: ComposerProps) {
  const [value, setValue] = useState('')

  const canSubmit = value.trim().length > 0 && !disabled

  const submit = () => {
    if (!canSubmit) return
    onSubmit(value)
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    submit()
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      submit()
    }
  }

  return (
    <div className="mx-auto grid w-full max-w-6xl grid-cols-1 gap-14 px-5 py-14 sm:px-8 sm:py-20 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:gap-10 lg:py-28">
      {/* Left: editorial masthead + copy */}
      <div className="animate-fade-up">
        <div className="mb-6 flex items-center gap-2.5 text-clay-600 dark:text-clay-400">
          <span className="h-px w-8 bg-current" />
          <span className="text-[11px] font-semibold uppercase tracking-[0.18em]">
            Multi-agent trip planning
          </span>
        </div>

        <h1 className="max-w-xl text-balance font-serif text-[2.75rem] leading-[1.05] font-medium tracking-tight text-stone-900 sm:text-6xl dark:text-stone-50">
          Where should we <em className="italic text-clay-600 dark:text-clay-400">send</em> you?
        </h1>

        <p className="mt-6 max-w-md text-balance text-[15.5px] leading-relaxed text-stone-500 dark:text-stone-400">
          Describe the trip in plain language — dates, destination, budget, vibe. A small crew of
          specialist agents takes it from there: flights, hotels, and a full day-by-day plan.
        </p>

        <dl className="mt-12 hidden max-w-md flex-col gap-6 sm:flex">
          {HOW_IT_WORKS.map((item) => (
            <div key={item.n} className="flex items-start gap-4">
              <dt className="font-serif text-sm text-clay-300 dark:text-clay-700" aria-hidden="true">
                {item.n}
              </dt>
              <dd className="flex-1">
                <div className="flex items-center gap-2">
                  <item.icon className="h-3.5 w-3.5 text-clay-500" strokeWidth={2} />
                  <p className="text-[13.5px] font-medium text-stone-700 dark:text-stone-200">
                    {item.title}
                  </p>
                </div>
                <p className="mt-1 text-[13px] leading-relaxed text-stone-400 dark:text-stone-500">
                  {item.detail}
                </p>
              </dd>
            </div>
          ))}
        </dl>
      </div>

      {/* Right: composer card */}
      <div className="animate-fade-up [animation-delay:120ms]">
        <form
          onSubmit={handleSubmit}
          className="relative rounded-[20px] border border-stone-900/[0.08] bg-white p-2 shadow-[0_1px_2px_rgba(20,14,8,0.04),0_16px_40px_-16px_rgba(120,60,20,0.22)] transition-shadow focus-within:shadow-[0_1px_2px_rgba(20,14,8,0.06),0_20px_48px_-16px_rgba(211,95,52,0.3)] dark:border-stone-100/10 dark:bg-stone-900"
        >
          <label
            htmlFor="trip-request"
            className="block px-4 pt-3 text-[11px] font-semibold uppercase tracking-[0.14em] text-stone-400 dark:text-stone-500"
          >
            Tell us about the trip
          </label>
          <textarea
            id="trip-request"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            rows={4}
            placeholder="Plan a 5 day trip to Tokyo under $1500, leaving from San Francisco…"
            className="w-full resize-none rounded-xl bg-transparent px-4 py-3 text-[15.5px] leading-relaxed text-stone-800 placeholder:text-stone-400 focus:outline-none disabled:opacity-60 dark:text-stone-100 dark:placeholder:text-stone-600"
          />
          <div className="flex items-center justify-between gap-3 px-3 pb-2 pt-1">
            <span className="hidden text-xs text-stone-400 sm:inline dark:text-stone-600">
              <kbd className="rounded border border-stone-200 bg-stone-50 px-1.5 py-0.5 font-sans dark:border-stone-700 dark:bg-stone-800">
                Enter
              </kbd>{' '}
              to plan
            </span>
            <button
              type="submit"
              disabled={!canSubmit}
              className="ml-auto inline-flex shrink-0 items-center gap-2 rounded-xl bg-clay-500 px-4 py-2.5 text-sm font-medium text-white shadow-[0_10px_20px_-8px_rgba(211,95,52,0.55)] transition-all duration-200 hover:-translate-y-px hover:bg-clay-600 hover:shadow-[0_14px_24px_-8px_rgba(211,95,52,0.6)] active:translate-y-0 active:scale-[0.98] disabled:translate-y-0 disabled:cursor-not-allowed disabled:bg-stone-200 disabled:text-stone-400 disabled:shadow-none dark:disabled:bg-stone-800 dark:disabled:text-stone-600"
            >
              Plan my trip
              <ArrowRight className="h-4 w-4" strokeWidth={2} />
            </button>
          </div>
        </form>

        <div className="mt-6">
          <p className="mb-2.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-stone-400 dark:text-stone-600">
            Or try one of these
          </p>
          <ul className="divide-y divide-stone-900/[0.06] overflow-hidden rounded-xl border border-stone-900/[0.08] bg-white/60 dark:divide-stone-100/10 dark:border-stone-100/10 dark:bg-stone-900/40">
            {EXAMPLE_PROMPTS.map((prompt) => (
              <li key={prompt}>
                <button
                  type="button"
                  disabled={disabled}
                  onClick={() => setValue(prompt)}
                  className="group flex w-full items-center justify-between gap-3 px-4 py-3 text-left text-[13.5px] text-stone-600 transition-colors hover:bg-clay-50 disabled:opacity-50 dark:text-stone-300 dark:hover:bg-clay-950/30"
                >
                  <span>{prompt}</span>
                  <ArrowUpRight className="h-3.5 w-3.5 shrink-0 text-stone-300 transition-all duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-clay-500 dark:text-stone-600" />
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
