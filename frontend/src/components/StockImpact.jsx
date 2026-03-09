/**
 * StockImpact — Shows predicted stock price impact based on script score.
 * Displays "current vs improved" comparison so users see the value of edits.
 */

const DIMENSION_LABELS = {
  sentiment: 'Sentiment',
  confidence: 'Confidence',
  ownership: 'Ownership',
  clarity: 'Clarity',
  red_flags: 'Red Flag Score',
}

function formatPct(val) {
  if (val == null) return '—'
  const sign = val >= 0 ? '+' : ''
  return `${sign}${val.toFixed(1)}%`
}

function pctColor(val) {
  if (val == null) return 'text-text-muted'
  if (val > 0.5) return 'text-success'
  if (val < -0.5) return 'text-danger'
  return 'text-warning'
}

function ImpactCard({ title, subtitle, data, accent }) {
  const borderClass = accent === 'primary' ? 'border-primary' : 'border-success'
  const bgClass = accent === 'primary' ? 'bg-primary/5' : 'bg-success/5'

  return (
    <div className={`flex-1 rounded-xl border-2 ${borderClass} ${bgClass} p-5`}>
      <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">{title}</p>
      <p className="mt-0.5 text-sm text-text-muted">{subtitle}</p>

      <div className="mt-4 flex items-baseline gap-1">
        <span className={`font-mono text-3xl font-bold ${pctColor(data.median_1d_pct)}`}>
          {formatPct(data.median_1d_pct)}
        </span>
        <span className="text-xs text-text-muted">next-day median</span>
      </div>

      <div className="mt-2 flex items-baseline gap-1">
        <span className={`font-mono text-lg font-semibold ${pctColor(data.median_2d_pct)}`}>
          {formatPct(data.median_2d_pct)}
        </span>
        <span className="text-xs text-text-muted">2-day median</span>
      </div>

      <div className="mt-3 rounded-lg bg-white/60 px-3 py-2">
        <p className="text-xs text-text-muted">
          Typical range: <span className="font-mono font-medium text-text-main">{formatPct(data.range_1d?.[0])}</span>
          {' '}to{' '}
          <span className="font-mono font-medium text-text-main">{formatPct(data.range_1d?.[1])}</span>
        </p>
      </div>
    </div>
  )
}

export default function StockImpact({ data }) {
  if (!data) return null

  const { current, improved, improvement_delta_1d, weakest_dimensions, disclaimer } = data

  return (
    <div className="mt-8">
      {/* Section header */}
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
          <svg className="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
          </svg>
        </div>
        <div>
          <h2 className="font-sora text-lg font-bold text-text-main">Predicted Stock Impact</h2>
          <p className="text-sm text-text-muted">Based on historical earnings call language patterns</p>
        </div>
      </div>

      {/* Current vs Improved cards */}
      <div className="mt-5 flex flex-col gap-4 sm:flex-row">
        <ImpactCard
          title="Current Script"
          subtitle={`Score ${current.overall_score} \u2014 ${current.label}`}
          data={current}
          accent="primary"
        />

        {/* Arrow connector */}
        <div className="flex items-center justify-center sm:flex-col">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-success/10">
            <svg className="h-5 w-5 text-success sm:rotate-0 rotate-90" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
            </svg>
          </div>
        </div>

        <ImpactCard
          title="With Suggested Edits"
          subtitle={`Projected score ${improved.overall_score} \u2014 ${improved.label}`}
          data={improved}
          accent="success"
        />
      </div>

      {/* Improvement delta callout */}
      {improvement_delta_1d != null && improvement_delta_1d > 0 && (
        <div className="mt-4 flex items-center gap-3 rounded-xl border border-success/30 bg-success/5 px-5 py-3.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-success/20">
            <svg className="h-4 w-4 text-success" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 10.5L12 3m0 0l7.5 7.5M12 3v18" />
            </svg>
          </div>
          <p className="text-sm font-medium text-text-main">
            Implementing suggested changes could shift the median next-day reaction by{' '}
            <span className="font-mono font-bold text-success">{formatPct(improvement_delta_1d)}</span>
          </p>
        </div>
      )}

      {/* Weakest dimensions */}
      {weakest_dimensions && weakest_dimensions.length > 0 && (
        <div className="mt-4 rounded-xl border border-border bg-white p-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">Top Improvement Areas</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {weakest_dimensions.map((dim) => (
              <div key={dim.dimension} className="flex items-center gap-2 rounded-lg bg-bg px-3 py-2">
                <div className="h-2 w-2 rounded-full bg-warning" />
                <span className="text-sm font-medium text-text-main">
                  {DIMENSION_LABELS[dim.dimension] || dim.dimension}
                </span>
                <span className="font-mono text-sm text-text-muted">{dim.score}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Disclaimer */}
      <p className="mt-4 text-center text-xs italic text-text-muted">
        {disclaimer}
      </p>
    </div>
  )
}
