import { useState, useRef, useCallback } from 'react'
import { Link } from 'react-router-dom'
import ScoreRing from '../components/ScoreRing'
import ScoreCard from '../components/ScoreCard'
import StockImpact from '../components/StockImpact'
import FlaggedIssue from '../components/FlaggedIssue'
import AnalystQA from '../components/AnalystQA'
import LitigationPanel from '../components/LitigationPanel'
import ExportButtons from '../components/ExportButtons'

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
  const fileRef = useRef(null)

  const ALLOWED_EXTS = ['txt', 'docx', 'md', 'pdf']

  const handleAnalyze = useCallback(async () => {
    setLoading(true)
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

      const res = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Analysis failed')
      }

      const data = await res.json()
      setResults(data)
      setActiveTab('flagged')
    } catch (err) {
      alert(err.message)
    } finally {
      setLoading(false)
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
    const { scores, stock_impact, flagged_issues, analyst_qa, negative_interpretations, litigation, activist_triggers, session_id } = results

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

          {/* Stock Impact Prediction */}
          <StockImpact data={stock_impact} />

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
        </div>
      </main>
    </div>
  )
}
