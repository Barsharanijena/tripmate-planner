import { RotateCcw, TriangleAlert } from 'lucide-react'

type ErrorStateProps = {
  message: string
  onRetry: () => void
  onStartOver: () => void
}

export function ErrorState({ message, onRetry, onStartOver }: ErrorStateProps) {
  return (
    <div className="w-full max-w-md animate-fade-up rounded-[20px] border border-rose-200/70 bg-white p-8 text-center shadow-[0_1px_2px_rgba(20,14,8,0.04),0_20px_44px_-20px_rgba(190,40,40,0.22)] dark:border-rose-900/40 dark:bg-stone-900">
      <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-rose-50 text-rose-600 dark:bg-rose-950/40 dark:text-rose-400">
        <TriangleAlert className="h-5.5 w-5.5" strokeWidth={1.8} />
      </span>
      <h2 className="mt-5 font-serif text-2xl font-medium tracking-tight text-stone-900 dark:text-stone-50">
        We hit a snag
      </h2>
      <p className="mx-auto mt-2.5 max-w-xs text-[14.5px] leading-relaxed text-stone-500 dark:text-stone-400">
        {message}
      </p>
      <div className="mt-7 flex items-center justify-center gap-3">
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 rounded-xl bg-clay-500 px-4 py-2.5 text-sm font-medium text-white shadow-[0_10px_20px_-8px_rgba(211,95,52,0.55)] transition-all duration-200 hover:-translate-y-px hover:bg-clay-600 active:translate-y-0 active:scale-[0.98]"
        >
          <RotateCcw className="h-3.5 w-3.5" strokeWidth={2} />
          Try again
        </button>
        <button
          type="button"
          onClick={onStartOver}
          className="rounded-xl border border-stone-200 bg-white px-4 py-2.5 text-sm font-medium text-stone-600 transition-colors hover:bg-stone-50 dark:border-stone-700 dark:bg-stone-900 dark:text-stone-300 dark:hover:bg-stone-800"
        >
          Start over
        </button>
      </div>
    </div>
  )
}
