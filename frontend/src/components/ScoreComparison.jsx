import { useState, useEffect } from 'react'

/**
 * ScoreComparison — Shows current score vs prior calls and peer group.
 * Prior comparison loads immediately; peer comparison loads async.
 */

const DIMENSION_LABELS = {
  sentiment: 'Sentiment',
  confidence: 'Confidence',
  ownership: 'Ownership',
  clarity: 'Clarity',
  red_flags: 'Red Flags',
}

function deltaColor(val) {
  if (val > 1) return 'text-success'
  if (val < -1) return 'text-danger'
  return 'text-text-muted'
}

function deltaBg(val) {
  if (val > 1) return 'bg-success/10 border-success/30'
  if (val < -1) return 'bg-danger/10 border-danger/30'
  return 'bg-gray-50 border-border'
}

function formatDelta(val) {
  if (val == null) return '—'
  const sign = val > 0 ? '+' : ''
  return `${sign}${val}`
}

function scoreColor(score) {
  if (score >= 75) return '#059669'
  if (score >= 50) return '#D97706'
  return '#DC2626'
}

function gradeFor(score) {
  if (score >= 93) return 'A'
  if (score >= 90) return 'A-'
  if (score >= 87) return 'B+'
  if (score >= 83) return 'B'
  if (score >= 80) return 'B-'
  if (score >= 77) return 'C+'
  if (score >= 73) return 'C'
  if (score >= 70) return 'C-'
  if (score >= 67) return 'D+'
  if (score >= 60) return 'D'
  return 'F'
}


function MiniScoreCard({ label, score, subtitle }) {
  const color = scoreColor(score)
  return (
    <div className="flex-1 rounded-xl border-2 p-5 text-center" style={{ borderColor: color + '40', backgroundColor: color + '08' }}>
      <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">{label}</p>
      {subtitle && <p className="mt-0.5 text-xs text-text-muted">{subtitle}</p>}
      <p className="mt-3 font-mono text-3xl font-bold" style={{ color }}>{score}</p>
      <p className="mt-1 text-sm font-semibold" style={{ color }}>{gradeFor(score)}</p>
    </div>
  )
}


function DeltaBadge({ value, label }) {
  return (
    <div className={`flex items-center gap-2 rounded-lg border px-3 py-2 ${deltaBg(value)}`}>
      <span className={`font-mono text-sm font-bold ${deltaColor(value)}`}>{formatDelta(value)}</span>
      <span className="text-xs text-text-muted">{label}</span>
    </div>
  )
}


function TrendBar({ priorScores, currentScore }) {
  // Show a simple horizontal bar chart of scores over time
  const allPoints = [...priorScores].reverse().concat([{ quarter: 'Current', scores: { overall: currentScore } }])

  return (
    <div className="mt-4 rounded-xl border border-border bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">Score Trend</p>
      <div className="mt-3 space-y-2">
        {allPoints.map((pt, i) => {
          const score = pt.scores.overall
          const isCurrent = i === allPoints.length - 1
          const color = scoreColor(score)
          return (
            <div key={pt.quarter} className="flex items-center gap-3">
              <span className={`w-20 text-xs ${isCurrent ? 'font-bold text-text-main' : 'text-text-muted'}`}>
                {pt.quarter}
              </span>
              <div className="flex-1 h-5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{ width: `${score}%`, backgroundColor: color }}
                />
              </div>
              <span className={`w-8 text-right font-mono text-xs font-bold`} style={{ color }}>
                {score}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}


function PeerLoadingSpinner() {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-border bg-white p-5">
      <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      <p className="text-sm text-text-muted">Analyzing peer group transcripts...</p>
    </div>
  )
}


export default function ScoreComparison({ currentScores, priorComparison, sessionId, ticker }) {
  const [peerData, setPeerData] = useState(null)
  const [peerLoading, setPeerLoading] = useState(false)
  const [peerError, setPeerError] = useState(null)

  // Fetch peer comparison async when session + ticker are available
  useEffect(() => {
    if (!sessionId || !ticker) return

    setPeerLoading(true)
    setPeerError(null)

    fetch(`/api/peer-comparison/${sessionId}`)
      .then((res) => {
        if (!res.ok) throw new Error('Peer comparison failed')
        return res.json()
      })
      .then((data) => {
        setPeerData(data)
      })
      .catch((err) => {
        setPeerError(err.message)
      })
      .finally(() => {
        setPeerLoading(false)
      })
  }, [sessionId, ticker])

  // Don't render anything if no ticker (no comparisons possible)
  if (!ticker) return null

  const hasPrior = priorComparison && priorComparison.vs_prior
  const hasPeerResults = peerData && peerData.peer_average

  return (
    <div className="mt-8">
      {/* Section header */}
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
          <svg className="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
          </svg>
        </div>
        <div>
          <h2 className="font-sora text-lg font-bold text-text-main">Score Comparison</h2>
          <p className="text-sm text-text-muted">How this script compares to prior calls and peers</p>
        </div>
      </div>

      {/* Prior Call Comparison */}
      {hasPrior && (
        <div className="mt-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3">
            vs. Prior Call ({priorComparison.vs_prior.quarter})
          </p>

          <div className="flex flex-col gap-4 sm:flex-row">
            <MiniScoreCard
              label="Current Script"
              score={currentScores.overall}
            />

            {/* Arrow connector */}
            <div className="flex items-center justify-center sm:flex-col">
              <div className={`flex h-10 w-10 items-center justify-center rounded-full ${deltaBg(priorComparison.vs_prior.overall_delta)}`}>
                <span className={`font-mono text-sm font-bold ${deltaColor(priorComparison.vs_prior.overall_delta)}`}>
                  {formatDelta(priorComparison.vs_prior.overall_delta)}
                </span>
              </div>
            </div>

            <MiniScoreCard
              label="Prior Call"
              subtitle={priorComparison.vs_prior.quarter}
              score={priorComparison.prior_scores[0]?.scores?.overall ?? 0}
            />
          </div>

          {/* Dimension deltas */}
          <div className="mt-3 flex flex-wrap gap-2">
            {Object.entries(priorComparison.vs_prior.dimension_deltas).map(([dim, delta]) => (
              <DeltaBadge key={dim} value={delta} label={DIMENSION_LABELS[dim] || dim} />
            ))}
          </div>

          {/* Trend chart (if multiple prior quarters) */}
          {priorComparison.prior_scores.length > 1 && (
            <TrendBar priorScores={priorComparison.prior_scores} currentScore={currentScores.overall} />
          )}
        </div>
      )}

      {!hasPrior && !peerLoading && !hasPeerResults && (
        <p className="mt-4 text-sm text-text-muted">No prior transcripts available for comparison.</p>
      )}

      {/* Peer Group Comparison */}
      <div className="mt-6">
        <p className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3">
          vs. Peer Group
        </p>

        {peerLoading && <PeerLoadingSpinner />}

        {peerError && !peerLoading && (
          <p className="text-sm text-text-muted">Peer comparison unavailable.</p>
        )}

        {hasPeerResults && (
          <>
            <div className="flex flex-col gap-4 sm:flex-row">
              <MiniScoreCard
                label="Current Script"
                score={currentScores.overall}
              />

              {/* Arrow connector */}
              <div className="flex items-center justify-center sm:flex-col">
                <div className={`flex h-10 w-10 items-center justify-center rounded-full ${deltaBg(peerData.vs_peer_group.overall_delta)}`}>
                  <span className={`font-mono text-sm font-bold ${deltaColor(peerData.vs_peer_group.overall_delta)}`}>
                    {formatDelta(peerData.vs_peer_group.overall_delta)}
                  </span>
                </div>
              </div>

              <MiniScoreCard
                label="Peer Group Avg"
                subtitle={`${peerData.peers_scored} peers scored`}
                score={peerData.peer_average.overall}
              />
            </div>

            {/* Headline callout */}
            <div className={`mt-4 flex items-center gap-3 rounded-xl border px-5 py-3.5 ${deltaBg(peerData.vs_peer_group.overall_delta)}`}>
              <p className="text-sm font-medium text-text-main">
                Overall score is{' '}
                <span className={`font-mono font-bold ${deltaColor(peerData.vs_peer_group.overall_delta)}`}>
                  {peerData.vs_peer_group.overall_pct_delta}
                </span>
                {' '}{peerData.vs_peer_group.overall_delta >= 0 ? 'above' : 'below'} peer group average
              </p>
            </div>

            {/* Dimension deltas */}
            <div className="mt-3 flex flex-wrap gap-2">
              {Object.entries(peerData.vs_peer_group.dimension_deltas).map(([dim, delta]) => (
                <DeltaBadge key={dim} value={delta} label={DIMENSION_LABELS[dim] || dim} />
              ))}
            </div>

            {/* Peer details (collapsible) */}
            <PeerDetailsTable peers={peerData.peer_details} />
          </>
        )}

        {!peerLoading && !peerError && !hasPeerResults && peerData && (
          <p className="text-sm text-text-muted">{peerData.error || 'No peer data available.'}</p>
        )}
      </div>
    </div>
  )
}


function PeerDetailsTable({ peers }) {
  const [expanded, setExpanded] = useState(false)

  if (!peers || peers.length === 0) return null

  return (
    <div className="mt-3 rounded-xl border border-border bg-white overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-gray-50 transition-colors"
      >
        <span className="text-xs font-semibold uppercase tracking-wider text-text-muted">
          Individual Peer Scores ({peers.length})
        </span>
        <svg
          className={`h-4 w-4 text-text-muted transition-transform ${expanded ? 'rotate-180' : ''}`}
          fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
        </svg>
      </button>

      {expanded && (
        <div className="border-t border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-xs text-text-muted uppercase">
                <th className="px-4 py-2 text-left">Ticker</th>
                <th className="px-4 py-2 text-left">Quarter</th>
                <th className="px-4 py-2 text-right">Overall</th>
                <th className="px-4 py-2 text-right">Grade</th>
              </tr>
            </thead>
            <tbody>
              {peers.map((peer) => (
                <tr key={peer.ticker} className="border-t border-border">
                  <td className="px-4 py-2 font-mono font-medium">{peer.ticker}</td>
                  <td className="px-4 py-2 text-text-muted">{peer.quarter}</td>
                  <td className="px-4 py-2 text-right font-mono font-bold" style={{ color: scoreColor(peer.scores.overall) }}>
                    {peer.scores.overall}
                  </td>
                  <td className="px-4 py-2 text-right font-semibold" style={{ color: scoreColor(peer.scores.overall) }}>
                    {gradeFor(peer.scores.overall)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
