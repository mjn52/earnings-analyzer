import { Link } from 'react-router-dom'

/* ------------------------------------------------------------------ */
/*  Inline SVG icons                                                   */
/* ------------------------------------------------------------------ */

function LogoIcon() {
  return (
    <svg viewBox="0 0 28 28" fill="none" className="h-7 w-7" aria-hidden="true">
      <rect x="2" y="16" width="4" height="10" rx="1" fill="#1A56DB" />
      <rect x="8" y="10" width="4" height="16" rx="1" fill="#1A56DB" opacity="0.8" />
      <rect x="14" y="6" width="4" height="20" rx="1" fill="#1A56DB" opacity="0.6" />
      <rect x="20" y="2" width="4" height="24" rx="1" fill="#1A56DB" opacity="0.4" />
    </svg>
  )
}

function IconUpload() {
  return (
    <svg className="h-8 w-8 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
    </svg>
  )
}

function IconAnalysis() {
  return (
    <svg className="h-8 w-8 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6" />
    </svg>
  )
}

function IconExport() {
  return (
    <svg className="h-8 w-8 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
    </svg>
  )
}

function IconSentiment() {
  return (
    <svg className="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6a7.5 7.5 0 107.5 7.5h-7.5V6z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 10.5H21A7.5 7.5 0 0013.5 3v7.5z" />
    </svg>
  )
}

function IconConfidence() {
  return (
    <svg className="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
    </svg>
  )
}

function IconLitigation() {
  return (
    <svg className="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v17.25m0 0c-1.472 0-2.882.265-4.185.75M12 20.25c1.472 0 2.882.265 4.185.75M18.75 4.97A48.416 48.416 0 0012 4.5c-2.291 0-4.545.16-6.75.47m13.5 0c1.01.143 2.01.317 3 .52m-3-.52l2.62 10.726c.122.499-.106 1.028-.589 1.202a5.988 5.988 0 01-2.031.352 5.988 5.988 0 01-2.031-.352c-.483-.174-.711-.703-.59-1.202L18.75 4.971zm-16.5.52c.99-.203 1.99-.377 3-.52m0 0l2.62 10.726c.122.499-.106 1.028-.589 1.202a5.989 5.989 0 01-2.031.352 5.989 5.989 0 01-2.031-.352c-.483-.174-.711-.703-.59-1.202L5.25 4.971z" />
    </svg>
  )
}

function IconQA() {
  return (
    <svg className="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 01-.825-.242m9.345-8.334a2.126 2.126 0 00-.476-.095 48.64 48.64 0 00-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0011.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155" />
    </svg>
  )
}

function IconNegative() {
  return (
    <svg className="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
    </svg>
  )
}

function IconActivist() {
  return (
    <svg className="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
    </svg>
  )
}

/* ------------------------------------------------------------------ */
/*  Landing Page                                                       */
/* ------------------------------------------------------------------ */

export default function Landing() {
  return (
    <div className="min-h-screen">
      {/* NAV */}
      <nav className="sticky top-0 z-50 border-b border-border bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2">
            <LogoIcon />
            <span className="font-sora text-lg font-bold text-text-main">StreetSignals</span>
          </div>

          <div className="hidden items-center gap-8 text-sm font-medium text-text-muted md:flex">
            <a href="#how-it-works" className="transition-colors hover:text-text-main">How It Works</a>
            <a href="#what-it-analyzes" className="transition-colors hover:text-text-main">What It Analyzes</a>
            <a href="#security" className="transition-colors hover:text-text-main">Security</a>
          </div>

          <div className="flex items-center gap-3">
            <button className="hidden rounded-lg border border-border px-4 py-2 text-sm font-medium text-text-muted transition-colors hover:border-primary hover:text-primary sm:inline-block">
              Sign In
            </button>
            <Link
              to="/analyze"
              className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-primary-dark"
            >
              Analyze Free&nbsp;&rarr;
            </Link>
          </div>
        </div>
      </nav>

      {/* HERO */}
      <section className="relative overflow-hidden bg-gradient-to-b from-bg to-[#EEF2FF] px-6 pb-24 pt-20 lg:pt-28">
        <div className="mx-auto max-w-4xl text-center">
          {/* Pill badge */}
          <div className="animate-fade-up mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-white px-4 py-1.5 text-sm text-text-muted shadow-sm">
            Pre-flight check for earnings calls&nbsp;&bull;
          </div>

          <h1
            className="animate-fade-up font-sora text-4xl font-bold leading-tight text-text-main md:text-5xl lg:text-6xl"
            style={{ animationDelay: '50ms' }}
          >
            Your script.{' '}
            <span className="bg-gradient-to-r from-primary to-blue-500 bg-clip-text text-transparent">
              Before the street hears it.
            </span>
          </h1>

          <p
            className="animate-fade-up mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-text-muted md:text-xl"
            style={{ animationDelay: '100ms' }}
          >
            Run your earnings call draft through 8 institutional-grade analyses — before a single analyst listens.
          </p>

          <div
            className="animate-fade-up mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row"
            style={{ animationDelay: '150ms' }}
          >
            <Link
              to="/analyze"
              className="inline-flex items-center gap-2 rounded-xl bg-primary px-8 py-3.5 text-base font-semibold text-white shadow-lg shadow-primary/25 transition-all hover:-translate-y-0.5 hover:bg-primary-dark hover:shadow-xl"
            >
              Analyze Your Script&nbsp;&rarr;
            </Link>
            <a
              href="#what-it-analyzes"
              className="inline-flex items-center gap-2 rounded-xl border border-border bg-white px-8 py-3.5 text-base font-medium text-text-main transition-colors hover:border-primary hover:text-primary"
            >
              What We Analyze&nbsp;&darr;
            </a>
          </div>
        </div>

        {/* Capability highlights — 4x2 grid */}
        <div className="mx-auto mt-16 max-w-5xl">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              {
                delay: '200ms',
                iconBg: 'bg-primary/10',
                iconColor: 'text-primary',
                iconPath: 'M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6',
                title: 'StreetSignals Score',
                desc: 'Overall grade combining sentiment, confidence, ownership, clarity & red flags',
              },
              {
                delay: '250ms',
                iconBg: 'bg-danger/10',
                iconColor: 'text-danger',
                iconPath: 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z',
                title: 'Litigation Risk Scan',
                desc: 'PSLRA safe harbor compliance and securities liability language check',
              },
              {
                delay: '300ms',
                iconBg: 'bg-warning/10',
                iconColor: 'text-warning',
                iconPath: 'M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z',
                title: 'Activist Vulnerability Scan',
                desc: 'Flags language patterns that shareholder activists target',
              },
              {
                delay: '350ms',
                iconBg: 'bg-primary/10',
                iconColor: 'text-primary',
                iconPath: 'M12 9v3.75m0-10.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z',
                title: 'Negative Interpretation Scan',
                desc: '18-pattern detector for language the street may read negatively',
              },
              {
                delay: '400ms',
                iconBg: 'bg-primary/10',
                iconColor: 'text-primary',
                iconPath: 'M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10',
                title: 'AI-Powered Rewrites',
                desc: 'Every flagged sentence gets a context-aware rewrite suggestion',
              },
              {
                delay: '450ms',
                iconBg: 'bg-success/10',
                iconColor: 'text-success',
                iconPath: 'M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z',
                title: 'Word & PDF Exports',
                desc: 'Download redline Word docs and color-coded PDFs for your team',
              },
              {
                delay: '500ms',
                iconBg: 'bg-success/10',
                iconColor: 'text-success',
                iconPath: 'M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941',
                title: 'Stock Impact Prediction',
                desc: 'See projected price reaction before and after suggested edits',
              },
              {
                delay: '550ms',
                iconBg: 'bg-warning/10',
                iconColor: 'text-warning',
                iconPath: 'M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z',
                title: 'Analyst Q&A Prep',
                desc: 'AI-generated tough questions with proposed answers to rehearse',
              },
            ].map((card, i) => (
              <div
                key={i}
                className="animate-fade-up rounded-xl border border-border bg-white p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md"
                style={{ animationDelay: card.delay }}
              >
                <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${card.iconBg}`}>
                  <svg className={`h-5 w-5 ${card.iconColor}`} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d={card.iconPath} />
                  </svg>
                </div>
                <p className="mt-3 text-sm font-semibold text-text-main">{card.title}</p>
                <p className="mt-1 text-xs leading-relaxed text-text-muted">{card.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how-it-works" className="bg-white px-6 py-20">
        <div className="mx-auto max-w-5xl">
          <h2 className="text-center font-sora text-3xl font-bold text-text-main">How It Works</h2>
          <p className="mx-auto mt-3 max-w-xl text-center text-text-muted">Three steps. Two seconds. Zero data leaves your machine.</p>

          <div className="mt-14 grid gap-12 md:grid-cols-3">
            {[
              {
                icon: <IconUpload />,
                title: 'Upload Your Script',
                desc: 'Paste or upload your draft. Nothing leaves your machine.',
              },
              {
                icon: <IconAnalysis />,
                title: '8-Dimension Analysis',
                desc: 'Scoring, risk scans, AI rewrites, stock prediction, Q&A prep, and more.',
              },
              {
                icon: <IconExport />,
                title: 'Export & Revise',
                desc: 'Download a color-coded PDF report and Word doc with tracked changes.',
              },
            ].map((step, i) => (
              <div key={i} className="text-center">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/5">{step.icon}</div>
                <h3 className="mt-5 font-sora text-lg font-semibold text-text-main">{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-text-muted">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* WHAT IT ANALYZES */}
      <section id="what-it-analyzes" className="bg-bg px-6 py-20">
        <div className="mx-auto max-w-5xl">
          <h2 className="text-center font-sora text-3xl font-bold text-text-main">What It Analyzes</h2>
          <p className="mx-auto mt-3 max-w-xl text-center text-text-muted">
            Eight research-backed analyses, each calibrated against institutional standards.
          </p>

          <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {[
              {
                icon: <IconSentiment />,
                title: 'StreetSignals Score',
                desc: 'Composite grade across sentiment, confidence, ownership, clarity & red flags.',
                source: 'LM Dictionary + Stanford Research',
              },
              {
                icon: <IconLitigation />,
                title: 'Litigation Risk Scan',
                desc: 'PSLRA safe harbor compliance and securities liability check.',
                source: 'Securities Lawyers',
              },
              {
                icon: <IconActivist />,
                title: 'Activist Vulnerability',
                desc: 'Shareholder activist language patterns and governance triggers.',
                source: 'Governance Research',
              },
              {
                icon: <IconNegative />,
                title: 'Negative Interpretation',
                desc: '18-pattern detector for language the street may read negatively.',
                source: 'Sell-Side Patterns',
              },
              {
                icon: <IconConfidence />,
                title: 'AI-Powered Rewrites',
                desc: 'Context-aware edit suggestions for every flagged sentence.',
                source: 'LLMs',
              },
              {
                icon: <IconExport />,
                title: 'Word & PDF Exports',
                desc: 'Redline Word docs and color-coded PDF reports for your team.',
                source: 'Industry-Standard Formats',
              },
              {
                icon: <IconAnalysis />,
                title: 'Stock Impact Prediction',
                desc: 'Projected price reaction based on historical language patterns.',
                source: 'Academic Research',
              },
              {
                icon: <IconQA />,
                title: 'Analyst Q&A Prep',
                desc: 'AI-generated tough questions with proposed answers to rehearse.',
                source: 'IR Best Practices',
              },
            ].map((card, i) => (
              <div
                key={i}
                className="rounded-xl border border-border bg-white p-6 transition-all hover:-translate-y-0.5 hover:shadow-md"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/5">{card.icon}</div>
                <h3 className="mt-4 font-sora text-base font-semibold text-text-main">{card.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-text-muted">{card.desc}</p>
                <p className="mt-3 text-xs text-text-muted/60">Powered by {card.source}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SECURITY / TRUST BAR */}
      <section id="security" className="bg-[#111827] px-6 py-20 text-white">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="font-sora text-3xl font-bold">Your data never leaves.</h2>
          <p className="mx-auto mt-4 max-w-xl text-lg text-gray-400">
            No API calls. No cloud processing. 100% local analysis. The same script that&rsquo;s running locally is what runs in our cloud.
          </p>

          <div className="mt-12 flex flex-wrap items-center justify-center gap-8 text-sm font-medium text-gray-300">
            <div className="flex items-center gap-2">
              <span className="text-lg">&#128274;</span> No Data Transmitted
            </div>
            <div className="flex items-center gap-2">
              <span className="text-lg">&#9889;</span> 2-Second Analysis
            </div>
            <div className="flex items-center gap-2">
              <span className="text-lg">&#128202;</span> Deterministic Results
            </div>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-border bg-white px-6 py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-2">
            <LogoIcon />
            <span className="font-sora text-sm font-bold text-text-main">StreetSignals</span>
          </div>
          <p className="text-sm text-text-muted">&copy; 2025 StreetSignals.ai</p>
        </div>
      </footer>
    </div>
  )
}
