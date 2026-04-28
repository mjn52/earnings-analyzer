import { useState, useRef, useCallback } from 'react'
import { Link } from 'react-router-dom'
import ScoreRing from '../components/ScoreRing'
import ScoreCard from '../components/ScoreCard'
import FlaggedIssue from '../components/FlaggedIssue'
import AnalystQA from '../components/AnalystQA'
import LitigationPanel from '../components/LitigationPanel'
import ExportButtons from '../components/ExportButtons'
import ScoreComparison from '../components/ScoreComparison'

/* ------------------------------------------------------------------ */
/*  Activist Triggers tab (inline — same pattern as LitigationPanel)   */
/* ------------------------------------------------------------------ */

const RISK_COLORS = {
  High: 'bg-danger text-white',
  Medium: 'bg-warning text-white',
  Low: 'bg-success text-white',
}

function ActivistTab({ data }) {
  if (!data) return null
  const { risk_level, triggers = [] } = data

  return (
    <div className="space-y-4">
      <span className={`inline-block rounded-full px-4 py-1.5 text-sm font-semibold ${RISK_COLORS[risk_level] || 'bg-gray-200 text-text-main'}`}>
        {risk_level} Risk
      </span>

      {triggers.map((t, i) => (
        <div key={i} className="rounded-xl border border-border bg-white p-4">
          <p className="text-sm font-semibold text-text-main">{t.trigger_type || t.category || 'Trigger'}</p>
          {t.original_text && <p className="mt-1 text-sm italic text-text-muted">&ldquo;{t.original_text}&rdquo;</p>}
          {t.activist_narrative && (
            <p className="mt-2 text-sm text-text-muted">
              <span className="font-medium text-danger">Activist narrative:</span> {t.activist_narrative}
            </p>
          )}
          {t.defense_suggestion && (
            <p className="mt-2 rounded-lg bg-bg px-3 py-2 text-sm text-text-muted">
              <span className="font-medium text-text-main">Defense:</span> {t.defense_suggestion}
            </p>
          )}
        </div>
      ))}

      {triggers.length === 0 && (
        <p className="py-8 text-center text-sm text-text-muted">No activist triggers detected.</p>
      )}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Negative Interpretations tab                                       */
/* ------------------------------------------------------------------ */

const CATEGORY_LABELS = {
  hedging_language: 'Hedging Language',
  vague_commitments: 'Vague Commitments',
  mixed_messaging: 'Mixed Messaging',
  defensiveness: 'Defensiveness',
  omission_signal: 'Omission Signal',
  metric_avoidance: 'Metric Avoidance',
  blame_shifting: 'Blame Shifting',
  over_promising: 'Over-Promising',
  vague_guidance: 'Vague Guidance',
  missing_guidance: 'Missing Guidance',
  guidance_gap: 'Guidance Gap',
  consensus_divergence: 'vs. Consensus',
}

function NegativeInterpTab({ items }) {
  if (!items || items.length === 0) {
    return <p className="py-8 text-center text-sm text-text-muted">No negative interpretations found.</p>
  }

  const severityColor = {
    high: 'border-l-danger',
    medium: 'border-l-warning',
    low: 'border-l-success',
  }

  return (
    <div className="space-y-3">
      {items.map((item, i) => (
        <div
          key={i}
          className={`rounded-xl border border-border border-l-4 bg-white p-4 ${severityColor[item.severity || item.risk_level] || ''}`}
        >
          <div className="flex items-center gap-2">
            {item.category && (
              <span className="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium tracking-wide text-text-muted">
                {CATEGORY_LABELS[item.category] || item.category.replace(/_/g, ' ')}
              </span>
            )}
            {(item.severity || item.risk_level) && (
              <span className="text-xs font-medium uppercase text-text-muted">
                {item.severity || item.risk_level}
              </span>
            )}
          </div>
          {item.original_text && (
            <p className="mt-2 text-sm italic text-text-muted">&ldquo;{item.original_text}&rdquo;</p>
          )}
          {item.negative_spin && (
            <p className="mt-2 text-sm text-text-muted">
              <span className="font-medium text-danger">Analyst spin:</span> {item.negative_spin}
            </p>
          )}
          {item.suggested_rewrite && (
            <p className="mt-2 rounded-lg bg-bg px-3 py-2 text-sm text-text-muted">
              <span className="font-medium text-text-main">Suggested rewrite:</span> {item.suggested_rewrite}
            </p>
          )}
        </div>
      ))}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Bull/Bear Case Defense card (shown above tabs when ticker provided) */
/* ------------------------------------------------------------------ */

function BullBearCard({ data }) {
  if (!data) return null
  const { bull_cases = [], bear_cases = [], rewrite_count = 0 } = data

  if (bull_cases.length === 0 && bear_cases.length === 0) return null

  return (
    <div className="mt-10">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
          <svg className="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v17.25m0 0c-1.472 0-2.882.265-4.185.75M12 20.25c1.472 0 2.882.265 4.185.75M18.75 4.97A48.416 48.416 0 0 0 12 4.5c-2.291 0-4.545.16-6.75.47m13.5 0c1.01.143 2.01.317 3 .52m-3-.52 2.62 10.726c.122.499-.106 1.028-.589 1.202a5.988 5.988 0 0 1-2.031.352 5.988 5.988 0 0 1-2.031-.352c-.483-.174-.711-.703-.59-1.202L18.75 4.971Zm-16.5.52c.99-.203 1.99-.377 3-.52m0 0 2.62 10.726c.122.499-.106 1.028-.589 1.202a5.989 5.989 0 0 1-2.031.352 5.989 5.989 0 0 1-2.031-.352c-.483-.174-.711-.703-.59-1.202L5.25 4.971Z" />
          </svg>
        </div>
        <div>
          <h2 className="font-sora text-lg font-bold text-text-main">
            Bull/Bear Case Defense
          </h2>
          <p className="text-sm text-text-muted">
            {rewrite_count} script rewrite{rewrite_count !== 1 ? 's' : ''} suggested to address investment cases
          </p>
        </div>
      </div>

      <div className="mt-5 flex flex-col gap-4 sm:flex-row">
        {/* Bull Cases */}
        <div className="flex-1 rounded-xl border-2 border-success bg-success/5 p-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-success">
            Bull Cases
          </p>
          <div className="mt-3 space-y-3">
            {bull_cases.map((c, i) => (
              <div key={i}>
                <p className="text-sm font-semibold text-text-main">{c.thesis}</p>
                <p className="mt-1 text-xs text-text-muted">{c.explanation}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Bear Cases */}
        <div className="flex-1 rounded-xl border-2 border-danger bg-danger/5 p-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-danger">
            Bear Cases
          </p>
          <div className="mt-3 space-y-3">
            {bear_cases.map((c, i) => (
              <div key={i}>
                <p className="text-sm font-semibold text-text-main">{c.thesis}</p>
                <p className="mt-1 text-xs text-text-muted">{c.explanation}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Main Analyzer Page                                                 */
/* ------------------------------------------------------------------ */

const TABS = [
  { key: 'flagged', label: 'Flagged Issues' },
  { key: 'qa', label: 'Analyst Q&A' },
  { key: 'negative', label: 'Negative Interpretations' },
  { key: 'litigation', label: 'Litigation Risk' },
  { key: 'activist', label: 'Activist Triggers' },
]

export default function Analyzer() {
  const [text, setText] = useState('')
  const [ticker, setTicker] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [activeTab, setActiveTab] = useState('flagged')
  const [dragOver, setDragOver] = useState(false)
  const [uploadedFile, setUploadedFile] = useState(null)
  const [progress, setProgress] = useState(null)
  const fileRef = useRef(null)

  const ALLOWED_EXTS = ['txt', 'docx', 'md', 'pdf']

  const handleAnalyze = useCallback(async () => {
    setLoading(true)
    setProgress({ progress: {}, timings: {}, elapsed_ms: 0, status: 'running' })
    try {
      const formData = new FormData()
      if (uploadedFile) {
        formData.append('file', uploadedFile)
      } else {
        formData.append('text', text)
      }
      if (ticker.trim()) {
        formData.append('ticker', ticker.trim().toUpperCase())
      }

      const startRes = await fetch('/api/analyze/start', {
        method: 'POST',
        body: formData,
      })
      if (!startRes.ok) {
        const err = await startRes.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to start analysis')
      }
      const { session_id } = await startRes.json()

      // Poll status until complete or failed. Cap at ~5 minutes.
      const deadline = Date.now() + 5 * 60 * 1000
      let status = 'running'
      while (status === 'running') {
        if (Date.now() > deadline) throw new Error('Analysis timed out after 5 minutes')
        await new Promise((r) => setTimeout(r, 800))
        const statusRes = await fetch(`/api/analyze/status/${session_id}`)
        if (!statusRes.ok) throw new Error('Lost connection to analysis')
        const snapshot = await statusRes.json()
        setProgress(snapshot)
        status = snapshot.status
        if (status === 'failed') throw new Error(snapshot.error || 'Analysis failed')
      }

      const resultRes = await fetch(`/api/analyze/result/${session_id}`)
      if (!resultRes.ok) {
        const err = await resultRes.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to fetch results')
      }
      const data = await resultRes.json()
      setResults(data)
      setActiveTab('flagged')
    } catch (err) {
      alert(err.message)
    } finally {
      setLoading(false)
      setProgress(null)
    }
  }, [text, ticker, uploadedFile])

  const handleFile = useCallback(
    (file) => {
      if (!file) return
      const ext = file.name.split('.').pop().toLowerCase()
      if (!ALLOWED_EXTS.includes(ext)) {
        alert('Please upload a .txt, .md, .docx, or .pdf file.')
        return
      }
      setUploadedFile(file)
      setText('')
    },
    []
  )

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault()
      setDragOver(false)
      const file = e.dataTransfer?.files?.[0]
      handleFile(file)
    },
    [handleFile]
  )

  const reset = () => {
    setResults(null)
    setText('')
    setTicker('')
    setUploadedFile(null)
  }

  // ---- RESULTS VIEW ----
  if (results) {
    const { scores, flagged_issues, analyst_qa, negative_interpretations, litigation, activist_triggers, bull_bear_cases, prior_comparison, session_id, ai_status } = results

    const SERVICE_LABELS = { qa: 'Analyst Q&A', rewrites: 'Sentence rewrites', analysis: 'Risk analysis', bull_bear: 'Bull/Bear cases' }
    const aiBanner = (() => {
      if (!ai_status) return null
      if (!ai_status.api_configured) {
        return { tone: 'red', title: 'AI analysis unavailable', detail: 'The server is not configured with an Anthropic API key — all sections below are showing template output, not AI-generated analysis.' }
      }
      if (ai_status.degraded && ai_status.degraded_services?.length) {
        const names = ai_status.degraded_services.map((s) => SERVICE_LABELS[s] || s).join(', ')
        return { tone: 'amber', title: 'Some AI features unavailable', detail: `${names} failed and fell back to template output. Results in these sections may be generic — try re-running the analysis, or check server logs if the issue persists.` }
      }
      return null
    })()

    const tabCounts = {
      flagged: flagged_issues?.length || 0,
      qa: analyst_qa?.total_questions || 0,
    }

    return (
      <div className="min-h-screen bg-bg">
        {/* Header */}
        <header className="border-b border-border bg-white">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
            <button onClick={reset} className="flex items-center gap-1 text-sm font-medium text-text-muted transition-colors hover:text-primary">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
              </svg>
              New Analysis
            </button>
            <span className="font-sora text-sm font-bold text-text-main">StreetSignals</span>
            <ExportButtons sessionId={session_id} />
          </div>
        </header>

        <main className="mx-auto max-w-5xl px-6 py-10">
          {aiBanner && (
            <div
              role="alert"
              className={`mb-6 flex items-start gap-3 rounded-lg border px-4 py-3 text-sm ${
                aiBanner.tone === 'red'
                  ? 'border-red-200 bg-red-50 text-red-900'
                  : 'border-amber-200 bg-amber-50 text-amber-900'
              }`}
            >
              <svg className="mt-0.5 h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
              </svg>
              <div>
                <div className="font-semibold">{aiBanner.title}</div>
                <div className="mt-0.5">{aiBanner.detail}</div>
              </div>
            </div>
          )}

          {/* Overall Score Hero */}
          <div className="flex justify-center">
            <div className="relative">
              <ScoreRing score={scores.overall} grade={scores.grade} />
            </div>
          </div>

          {/* Dimension Score Cards */}
          <div className="mt-10 flex flex-wrap gap-3">
            {['sentiment', 'confidence', 'ownership', 'clarity', 'red_flags'].map((dim) => (
              <ScoreCard key={dim} dimension={dim} score={scores[dim]} />
            ))}
          </div>

          {/* Score Comparison (vs. Prior Calls) */}
          <ScoreComparison
            currentScores={scores}
            priorComparison={prior_comparison}
            ticker={ticker}
          />

          {/* Bull/Bear Case Defense */}
          <BullBearCard data={bull_bear_cases} />

          {/* Tab Navigation */}
          <div className="mt-10 flex gap-1 overflow-x-auto border-b border-border">
            {TABS.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`whitespace-nowrap border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === tab.key
                    ? 'border-primary text-primary'
                    : 'border-transparent text-text-muted hover:text-text-main'
                }`}
              >
                {tab.label}
                {tabCounts[tab.key] != null && (
                  <span className="ml-1.5 rounded-full bg-gray-100 px-2 py-0.5 text-xs">
                    {tabCounts[tab.key]}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="mt-6">
            {activeTab === 'flagged' && (
              <div className="space-y-3">
                {flagged_issues?.map((issue, i) => (
                  <FlaggedIssue key={i} issue={issue} />
                ))}
                {(!flagged_issues || flagged_issues.length === 0) && (
                  <p className="py-8 text-center text-sm text-text-muted">No flagged issues found.</p>
                )}
              </div>
            )}
            {activeTab === 'qa' && <AnalystQA data={analyst_qa} />}
            {activeTab === 'negative' && <NegativeInterpTab items={negative_interpretations} />}
            {activeTab === 'litigation' && <LitigationPanel data={litigation} />}
            {activeTab === 'activist' && <ActivistTab data={activist_triggers} />}
          </div>
        </main>
      </div>
    )
  }

  // ---- INPUT VIEW ----
  return (
    <div className="flex min-h-screen flex-col bg-bg">
      {/* Minimal nav */}
      <header className="border-b border-border bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link to="/" className="flex items-center gap-2">
            <svg viewBox="0 0 28 28" fill="none" className="h-7 w-7">
              <rect x="2" y="16" width="4" height="10" rx="1" fill="#1A56DB" />
              <rect x="8" y="10" width="4" height="16" rx="1" fill="#1A56DB" opacity="0.8" />
              <rect x="14" y="6" width="4" height="20" rx="1" fill="#1A56DB" opacity="0.6" />
              <rect x="20" y="2" width="4" height="24" rx="1" fill="#1A56DB" opacity="0.4" />
            </svg>
            <span className="font-sora text-lg font-bold text-text-main">StreetSignals</span>
          </Link>
        </div>
      </header>

      <main className="flex flex-1 items-start justify-center px-6 pt-16">
        <div className="w-full max-w-2xl">
          <h1 className="text-center font-sora text-3xl font-bold text-text-main">Analyze Your Script</h1>
          <p className="mt-2 text-center text-sm text-text-muted">Upload a file or paste your transcript below.</p>

          {/* Drop zone */}
          <div
            className={`mt-8 flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-colors ${
              dragOver ? 'border-primary bg-primary/5' : uploadedFile ? 'border-primary/50 bg-primary/5' : 'border-border bg-white hover:border-primary/50'
            }`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileRef.current?.click()}
          >
            {uploadedFile ? (
              <>
                <svg className="h-8 w-8 text-success" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="mt-3 text-sm font-medium text-text-main">{uploadedFile.name}</p>
                <p className="mt-1 text-xs text-text-muted">Click to replace, or enter your ticker below and hit Run Analysis</p>
              </>
            ) : (
              <>
                <svg className="h-8 w-8 text-text-muted" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
                <p className="mt-3 text-sm font-medium text-text-main">
                  Drop your file here, or click to upload
                </p>
                <p className="mt-1 text-xs text-text-muted">.txt, .docx, .pdf, or .md</p>
              </>
            )}
            <input
              ref={fileRef}
              type="file"
              accept=".txt,.docx,.md,.pdf"
              className="hidden"
              onChange={(e) => { handleFile(e.target.files?.[0]); e.target.value = '' }}
            />
          </div>

          <div className="my-6 flex items-center gap-4">
            <div className="h-px flex-1 bg-border" />
            <span className="text-xs text-text-muted">or</span>
            <div className="h-px flex-1 bg-border" />
          </div>

          {/* Text area */}
          <div className="relative">
            <textarea
              value={text}
              onChange={(e) => { setText(e.target.value); if (e.target.value) setUploadedFile(null) }}
              placeholder="Paste your script directly..."
              className="h-48 w-full resize-none rounded-xl border border-border bg-white px-4 py-3 text-sm leading-relaxed text-text-main placeholder:text-text-muted/50 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
            <span className="absolute bottom-3 right-3 font-mono text-xs text-text-muted">
              {text.length.toLocaleString()} characters
            </span>
          </div>

          {/* Ticker input */}
          <div className="mt-4">
            <label className="mb-1.5 flex items-center gap-2 text-sm font-medium text-text-main">
              <svg className="h-4 w-4 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
              </svg>
              Company Ticker
              <span className="font-normal text-text-muted">(optional)</span>
            </label>
            <div className="flex items-center gap-3">
              <input
                type="text"
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                placeholder="e.g. AAPL"
                maxLength={10}
                className="w-32 rounded-lg border border-border bg-white px-3 py-2.5 font-mono text-sm uppercase tracking-wider text-text-main placeholder:text-text-muted/40 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              />
              <p className="text-xs text-text-muted">
                Enter the company's ticker to auto-fetch prior earnings calls for smarter Q&A predictions
              </p>
            </div>
          </div>

          {/* Analyze button */}
          <button
            onClick={handleAnalyze}
            disabled={loading || (!uploadedFile && text.length < 100)}
            className={`mt-6 w-full rounded-xl py-3.5 text-base font-semibold text-white transition-all ${
              loading
                ? 'btn-shimmer cursor-wait'
                : (!uploadedFile && text.length < 100)
                ? 'cursor-not-allowed bg-primary/40'
                : 'bg-primary shadow-lg shadow-primary/25 hover:-translate-y-0.5 hover:bg-primary-dark hover:shadow-xl'
            }`}
          >
            {loading ? (
              <span>
                Analyzing<span className="dots"></span>
              </span>
            ) : (
              <>Run Analysis&nbsp;&rarr;</>
            )}
          </button>

          {!uploadedFile && text.length > 0 && text.length < 100 && (
            <p className="mt-2 text-center text-xs text-text-muted">
              Minimum 100 characters required ({100 - text.length} more needed)
            </p>
          )}

          {loading && progress && <AnalysisProgress progress={progress} />}
        </div>
      </main>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  AnalysisProgress — live per-call status while /api/analyze runs    */
/* ------------------------------------------------------------------ */

const PROGRESS_LABELS = {
  qa: 'Analyst Q&A',
  rewrites: 'Sentence rewrites',
  analysis: 'Risk analysis',
  bull_bear: 'Bull / Bear cases',
  qc_review: 'Quality review',
}

const PROGRESS_ORDER = ['qa', 'rewrites', 'analysis', 'bull_bear', 'qc_review']

function AnalysisProgress({ progress }) {
  const items = progress?.progress || {}
  const timings = progress?.timings || {}
  const elapsed = Math.round((progress?.elapsed_ms || 0) / 1000)

  return (
    <div className="mt-6 rounded-xl border border-border bg-white p-4">
      <div className="mb-3 flex items-center justify-between text-xs text-text-muted">
        <span className="font-semibold uppercase tracking-wider">Analyzing</span>
        <span className="font-mono">{elapsed}s</span>
      </div>
      <ul className="space-y-2">
        {PROGRESS_ORDER.map((key) => {
          const state = items[key] || 'pending'
          const time = timings[key]
          // Hide skipped rows — showing "(skipped)" for things that don't apply
          // (no flagged sentences, no ticker provided) would be misleading,
          // since the doc still includes rewrites from the other Claude calls.
          if (state === 'skipped') return null
          return (
            <li key={key} className="flex items-center gap-3 text-sm">
              <ProgressIcon state={state} />
              <span
                className={
                  state === 'complete'
                    ? 'text-text-main'
                    : state === 'failed'
                    ? 'text-danger'
                    : state === 'running'
                    ? 'text-text-main'
                    : 'text-text-muted'
                }
              >
                {PROGRESS_LABELS[key]}
              </span>
              {state === 'complete' && time != null && (
                <span className="font-mono text-xs text-text-muted">{(time / 1000).toFixed(1)}s</span>
              )}
              {state === 'failed' && <span className="text-xs text-danger">failed</span>}
            </li>
          )
        })}
      </ul>
    </div>
  )
}

function ProgressIcon({ state }) {
  if (state === 'complete') {
    return (
      <svg className="h-4 w-4 flex-shrink-0 text-success" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
      </svg>
    )
  }
  if (state === 'failed') {
    return (
      <svg className="h-4 w-4 flex-shrink-0 text-danger" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
      </svg>
    )
  }
  if (state === 'running') {
    return (
      <svg className="h-4 w-4 flex-shrink-0 animate-spin text-primary" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeOpacity="0.25" />
        <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
      </svg>
    )
  }
  if (state === 'skipped') {
    return (
      <svg className="h-4 w-4 flex-shrink-0 text-text-muted/50" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14" />
      </svg>
    )
  }
  return <span className="h-4 w-4 flex-shrink-0 rounded-full border-2 border-border" />
}
