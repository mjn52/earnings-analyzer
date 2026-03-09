function scoreColor(score) {
  if (score >= 75) return 'text-success'
  if (score >= 50) return 'text-warning'
  return 'text-danger'
}

const STATUS_STYLES = {
  above: { label: 'Above', bg: 'bg-success/10', text: 'text-success', ring: 'ring-success/30' },
  inline: { label: 'Inline', bg: 'bg-success/10', text: 'text-success', ring: 'ring-success/30' },
  low_end: { label: 'Low End', bg: 'bg-warning/10', text: 'text-warning', ring: 'ring-warning/30' },
  below: { label: 'Below', bg: 'bg-danger/10', text: 'text-danger', ring: 'ring-danger/30' },
  missing: { label: 'Not Given', bg: 'bg-gray-100', text: 'text-text-muted', ring: 'ring-gray-200' },
  unknown: { label: '—', bg: 'bg-gray-50', text: 'text-text-muted', ring: 'ring-gray-200' },
}

function StatusPill({ status }) {
  const s = STATUS_STYLES[status] || STATUS_STYLES.unknown
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${s.bg} ${s.text} ${s.ring}`}>
      {s.label}
    </span>
  )
}

export default function GuidanceTable({ data }) {
  if (!data) return null

  const { clarity_score, grade, metrics = [], has_consensus, no_guidance_given, positive_signals = [], negative_signals = [] } = data

  // Backward compat: if data has old `detail` shape, use old format
  const isNewFormat = Array.isArray(metrics)
  const posSignals = positive_signals
  const negSignals = negative_signals

  return (
    <div className="space-y-4">
      {/* Score badge */}
      <div className="flex items-center gap-4">
        <div className="rounded-xl border border-border bg-white px-5 py-3 text-center">
          <p className={`font-mono text-2xl font-bold ${scoreColor(clarity_score)}`}>{clarity_score}</p>
          <p className="text-xs text-text-muted">Clarity Score</p>
        </div>
        <div className="rounded-xl border border-border bg-white px-5 py-3 text-center">
          <p className={`font-sora text-2xl font-bold ${scoreColor(clarity_score)}`}>{grade}</p>
          <p className="text-xs text-text-muted">Grade</p>
        </div>
      </div>

      {/* No guidance state */}
      {no_guidance_given && (
        <div className="rounded-xl border border-border bg-white p-6 text-center">
          <svg className="mx-auto h-8 w-8 text-text-muted" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          <p className="mt-2 text-sm font-medium text-text-main">No Forward Guidance Provided</p>
          <p className="mt-1 text-xs text-text-muted">This script does not contain specific forward-looking guidance or outlook metrics.</p>
        </div>
      )}

      {/* Metrics table — new format */}
      {isNewFormat && metrics.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-border bg-white">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-border bg-bg">
                <th className="px-4 py-3 font-medium text-text-muted">Metric</th>
                <th className="px-4 py-3 font-medium text-text-muted">Company Guidance</th>
                {has_consensus && (
                  <th className="px-4 py-3 font-medium text-text-muted">Consensus</th>
                )}
                <th className="px-4 py-3 font-medium text-text-muted">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {metrics.map((m, i) => (
                <tr key={i}>
                  <td className="px-4 py-3 font-medium text-text-main">{m.metric}</td>
                  <td className="px-4 py-3">
                    {m.company_guidance ? (
                      <div>
                        <span className="font-mono text-text-main">{m.company_guidance}</span>
                        {m.quote && (
                          <p className="mt-0.5 text-xs italic text-text-muted line-clamp-2">
                            &ldquo;{m.quote}&rdquo;
                          </p>
                        )}
                      </div>
                    ) : (
                      <span className="text-text-muted">—</span>
                    )}
                  </td>
                  {has_consensus && (
                    <td className="px-4 py-3 font-mono text-text-muted">
                      {m.consensus || '—'}
                    </td>
                  )}
                  <td className="px-4 py-3">
                    <StatusPill status={m.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {!has_consensus && (
            <div className="border-t border-border bg-bg px-4 py-2">
              <p className="text-xs text-text-muted">
                Consensus estimates unavailable. Enter a ticker symbol to compare guidance against analyst consensus.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Positive signals */}
      {posSignals.length > 0 && (
        <div className="rounded-xl border border-border bg-white p-4">
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-success">Positive Signals</p>
          <ul className="list-inside list-disc space-y-1 text-sm text-text-muted">
            {posSignals.map((s, i) => (
              <li key={i}>{typeof s === 'string' ? s : s.signal || String(s)}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Negative signals */}
      {negSignals.length > 0 && (
        <div className="rounded-xl border border-border bg-white p-4">
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-danger">Negative Signals</p>
          <ul className="list-inside list-disc space-y-1 text-sm text-text-muted">
            {negSignals.map((s, i) => (
              <li key={i}>{typeof s === 'string' ? s : s.signal || String(s)}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
