import { useState } from 'react'

const BAR_COLORS = {
  RED: 'bg-danger',
  YELLOW: 'bg-warning',
  GREEN: 'bg-success',
}

export default function FlaggedIssue({ issue }) {
  const [expanded, setExpanded] = useState(false)
  const barColor = BAR_COLORS[issue.color] || 'bg-gray-300'

  return (
    <div
      className="flex cursor-pointer overflow-hidden rounded-xl border border-border bg-white transition-all hover:shadow-sm"
      onClick={() => setExpanded(!expanded)}
    >
      <div className={`w-1.5 shrink-0 ${barColor}`} />
      <div className="flex-1 p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex flex-wrap gap-2">
            {issue.issues.map((label, i) => (
              <span
                key={i}
                className="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-text-main"
              >
                {label}
              </span>
            ))}
          </div>
          <svg
            className={`h-4 w-4 shrink-0 text-text-muted transition-transform ${expanded ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={2}
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
          </svg>
        </div>

        <p className={`mt-2 text-sm leading-relaxed text-text-muted ${expanded ? '' : 'line-clamp-2'}`}>
          &ldquo;{issue.sentence}&rdquo;
        </p>

        {expanded && issue.suggested_rewrite && issue.suggested_rewrite !== issue.sentence && (
          <div className="mt-3 rounded-lg bg-bg p-3">
            <p className="mb-1 text-xs font-medium uppercase tracking-wide text-text-muted">Suggested Rewrite</p>
            <p className="text-sm leading-relaxed text-text-main">{issue.suggested_rewrite}</p>
            <button
              onClick={(e) => {
                e.stopPropagation()
                navigator.clipboard.writeText(issue.suggested_rewrite)
              }}
              className="mt-2 rounded-md bg-primary/5 px-3 py-1 text-xs font-medium text-primary transition-colors hover:bg-primary/10"
            >
              Copy rewrite
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
