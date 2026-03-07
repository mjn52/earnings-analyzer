const RISK_COLORS = {
  High: 'bg-danger text-white',
  Medium: 'bg-warning text-white',
  Low: 'bg-success text-white',
}

export default function LitigationPanel({ data }) {
  if (!data) return null

  const { risk_level, risk_score, has_safe_harbor, findings = [] } = data

  return (
    <div className="space-y-4">
      {/* Header badges */}
      <div className="flex flex-wrap items-center gap-4">
        <span className={`rounded-full px-4 py-1.5 text-sm font-semibold ${RISK_COLORS[risk_level] || 'bg-gray-200 text-text-main'}`}>
          {risk_level} Risk
        </span>
        {risk_score != null && (
          <span className="font-mono text-sm text-text-muted">Score: {risk_score}/100</span>
        )}
      </div>

      {/* Safe harbor */}
      <div className="flex items-center gap-3 rounded-xl border border-border bg-white p-4">
        {has_safe_harbor ? (
          <>
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-success/10 text-success text-lg">&#10003;</span>
            <div>
              <p className="text-sm font-semibold text-text-main">Safe Harbor Statement Present</p>
              <p className="text-xs text-text-muted">PSLRA-compliant forward-looking statement disclaimer detected.</p>
            </div>
          </>
        ) : (
          <>
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-danger/10 text-danger text-lg">&#10007;</span>
            <div>
              <p className="text-sm font-semibold text-text-main">No Safe Harbor Statement</p>
              <p className="text-xs text-text-muted">Consider adding a PSLRA-compliant disclaimer.</p>
            </div>
          </>
        )}
      </div>

      {/* Findings */}
      {findings.map((finding, i) => (
        <div key={i} className="rounded-xl border border-border bg-white p-4">
          <p className="text-sm font-semibold text-text-main">{finding.issue || finding.risk_type || 'Finding'}</p>
          {finding.detail && <p className="mt-1 text-sm text-text-muted">{finding.detail}</p>}
          {finding.original_text && <p className="mt-1 text-sm italic text-text-muted">&ldquo;{finding.original_text}&rdquo;</p>}
          {finding.recommendation && (
            <p className="mt-2 rounded-lg bg-bg px-3 py-2 text-sm text-text-muted">
              <span className="font-medium text-text-main">Recommendation:</span> {finding.recommendation}
            </p>
          )}
          {finding.suggested_fix && (
            <p className="mt-2 rounded-lg bg-bg px-3 py-2 text-sm text-text-muted">
              <span className="font-medium text-text-main">Suggested Fix:</span> {finding.suggested_fix}
            </p>
          )}
        </div>
      ))}

      {findings.length === 0 && (
        <p className="py-8 text-center text-sm text-text-muted">No litigation risk findings.</p>
      )}
    </div>
  )
}
