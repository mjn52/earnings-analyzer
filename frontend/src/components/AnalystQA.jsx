import { useState } from 'react'

function ConfidenceBar({ value }) {
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-gray-100">
        <div
          className="h-full rounded-full bg-primary transition-all"
          style={{ width: `${Math.round(value * 100)}%` }}
        />
      </div>
      <span className="font-mono text-xs text-text-muted">{Math.round(value * 100)}%</span>
    </div>
  )
}

function QuestionCard({ question, answer, index }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div
      className="cursor-pointer rounded-xl border border-border bg-white p-4 transition-all hover:shadow-sm"
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start gap-3">
        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 font-mono text-xs font-bold text-primary">
          {index + 1}
        </span>
        <div className="flex-1">
          <p className="text-sm font-medium leading-relaxed text-text-main">{question.question}</p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {question.topic && (
              <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium uppercase tracking-wide text-primary">
                {question.topic}
              </span>
            )}
            {question.confidence != null && <ConfidenceBar value={question.confidence} />}
          </div>
        </div>
        <svg
          className={`h-4 w-4 shrink-0 text-text-muted transition-transform ${expanded ? 'rotate-180' : ''}`}
          fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
        </svg>
      </div>

      {expanded && answer && (
        <div className="ml-9 mt-4 space-y-3 border-t border-border pt-4">
          {answer.answer_strategy && (
            <div>
              <span className="rounded-full bg-success/10 px-2.5 py-0.5 text-xs font-medium text-success">
                {answer.answer_strategy}
              </span>
            </div>
          )}

          {answer.proposed_answer && (
            <div>
              <p className="mb-1 text-xs font-medium uppercase tracking-wide text-text-muted">Answer Framework</p>
              <p className="text-sm leading-relaxed text-text-muted">{answer.proposed_answer}</p>
            </div>
          )}

          {answer.key_data_points && answer.key_data_points.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-medium uppercase tracking-wide text-text-muted">Key Data Points</p>
              <ul className="list-inside list-disc space-y-1 text-sm text-text-muted">
                {answer.key_data_points.map((pt, i) => (
                  <li key={i}>{pt}</li>
                ))}
              </ul>
            </div>
          )}

          {answer.caution_notes && (
            <div className="rounded-lg bg-warning/5 p-3">
              <p className="text-xs font-medium text-warning">Caution</p>
              <p className="mt-0.5 text-sm text-text-muted">{answer.caution_notes}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function AnalystQA({ data }) {
  if (!data) return null
  const { questions = [], answers = [] } = data

  return (
    <div className="space-y-3">
      {questions.map((q, i) => (
        <QuestionCard key={i} question={q} answer={answers[i]} index={i} />
      ))}
      {questions.length === 0 && (
        <p className="py-8 text-center text-sm text-text-muted">No analyst questions predicted for this transcript.</p>
      )}
    </div>
  )
}
