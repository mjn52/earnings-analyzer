function scoreColor(score) {
  if (score >= 75) return 'text-success'
  if (score >= 50) return 'text-warning'
  return 'text-danger'
}

export default function GuidanceTable({ data }) {
  if (!data) return null

  const { clarity_score, grade, detail } = data
  const metrics = detail?.metrics_covered || []
  const missing = detail?.metrics_missing || []

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
                const metricName = typeof m === 'string' ? m : m.metric || m.name || m
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
                const metricName = typeof m === 'string' ? m : m.metric || m.name || m
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

      {/* Positive / Negative signals */}
      {detail?.positive_signals?.length > 0 && (
        <div className="rounded-xl border border-border bg-white p-4">
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-success">Positive Signals</p>
          <ul className="list-inside list-disc space-y-1 text-sm text-text-muted">
            {detail.positive_signals.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}

      {detail?.negative_signals?.length > 0 && (
        <div className="rounded-xl border border-border bg-white p-4">
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-danger">Negative Signals</p>
          <ul className="list-inside list-disc space-y-1 text-sm text-text-muted">
            {detail.negative_signals.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
