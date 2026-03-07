function scoreColor(score) {
  if (score >= 75) return 'text-success'
  if (score >= 50) return 'text-warning'
  return 'text-danger'
}

function severityColor(severity) {
  if (severity === 'high') return 'text-danger'
  if (severity === 'medium') return 'text-warning'
  return 'text-text-muted'
}

export default function GuidanceTable({ data }) {
  if (!data) return null

  const { clarity_score, grade, detail } = data
  const metrics = detail?.metrics_covered || []
  const missing = detail?.metrics_missing || []
  const findings = detail?.findings || []
  const posSignals = detail?.positive_signals || []
  const negSignals = detail?.negative_signals || []

  const hasContent = metrics.length > 0 || missing.length > 0 || findings.length > 0 || posSignals.length > 0 || negSignals.length > 0

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

      {/* Empty state */}
      {!hasContent && (
        <div className="rounded-xl border border-border bg-white p-6 text-center text-sm text-text-muted">
          No guidance metrics detected in this transcript.
        </div>
      )}

      {/* Metrics table */}
      {(metrics.length > 0 || missing.length > 0) && (
        <div className="overflow-hidden rounded-xl border border-border bg-white">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-border bg-bg">
                <th className="px-4 py-3 font-medium text-text-muted">Metric</th>
                <th className="px-4 py-3 font-medium text-text-muted">Status</th>
                <th className="px-4 py-3 font-medium text-text-muted">Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {metrics.map((m, i) => {
                const metricName = typeof m === 'string' ? m : m.metric || m.name || String(m)
                const quantified = typeof m === 'object' && m.quantified
                return (
                  <tr key={i}>
                    <td className="px-4 py-3 font-medium text-text-main capitalize">{metricName}</td>
                    <td className="px-4 py-3">
                      {quantified ? (
                        <span className="text-success">&#10003; Quantified</span>
                      ) : (
                        <span className="text-warning">&#9888; Qualitative</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-text-muted">
                      {typeof m === 'object' && m.notes ? m.notes : '—'}
                    </td>
                  </tr>
                )
              })}
              {missing.map((m, i) => {
                const metricName = typeof m === 'string' ? m : m.metric || m.name || String(m)
                return (
                  <tr key={`miss-${i}`}>
                    <td className="px-4 py-3 font-medium text-text-main capitalize">{metricName}</td>
                    <td className="px-4 py-3">
                      <span className="text-danger">&#10007; Missing</span>
                    </td>
                    <td className="px-4 py-3 text-text-muted">Not mentioned</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Findings */}
      {findings.length > 0 && (
        <div className="rounded-xl border border-border bg-white p-4">
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-text-muted">Findings</p>
          <ul className="space-y-2 text-sm">
            {findings.map((f, i) => {
              const issue = typeof f === 'string' ? f : f.issue || f.detail || String(f)
              const severity = typeof f === 'object' ? f.severity : null
              return (
                <li key={i} className="flex items-start gap-2">
                  {severity && (
                    <span className={`mt-0.5 shrink-0 text-xs font-medium uppercase ${severityColor(severity)}`}>
                      [{severity}]
                    </span>
                  )}
                  <span className="text-text-muted">{issue}</span>
                </li>
              )
            })}
          </ul>
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
