function scoreColor(score) {
  if (score >= 75) return 'text-success'
  if (score >= 50) return 'text-warning'
  return 'text-danger'
}

function barColor(score) {
  if (score >= 75) return 'bg-success'
  if (score >= 50) return 'bg-warning'
  return 'bg-danger'
}

const WEIGHTS = {
  sentiment: '25%',
  confidence: '25%',
  ownership: '15%',
  clarity: '15%',
  red_flags: '20%',
}

const LABELS = {
  sentiment: 'Sentiment',
  confidence: 'Confidence',
  ownership: 'Ownership',
  clarity: 'Clarity',
  red_flags: 'Red Flag Score',
}

export default function ScoreCard({ dimension, score }) {
  return (
    <div className="flex-1 rounded-xl border border-border bg-white p-4 text-center transition-all hover:-translate-y-0.5 hover:shadow-md">
      <p className={`font-mono text-2xl font-bold ${scoreColor(score)}`}>{score}</p>
      <p className="mt-1 text-sm font-medium text-text-main">{LABELS[dimension] || dimension}</p>
      <div className="mx-auto mt-2 h-1.5 w-full max-w-[80px] overflow-hidden rounded-full bg-gray-100">
        <div
          className={`h-full rounded-full ${barColor(score)} transition-all duration-500`}
          style={{ width: `${score}%` }}
        />
      </div>
      <p className="mt-2 text-xs text-text-muted">{WEIGHTS[dimension] || ''} of overall</p>
    </div>
  )
}
