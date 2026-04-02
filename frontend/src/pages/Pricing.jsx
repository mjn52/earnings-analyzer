import { Link } from 'react-router-dom'
import { useState } from 'react'

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

function CheckIcon() {
  return (
    <svg className="mt-0.5 h-5 w-5 flex-shrink-0 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
    </svg>
  )
}

export default function Pricing() {
  const [showWaitlist, setShowWaitlist] = useState(false)
  const [waitlistEmail, setWaitlistEmail] = useState('')
  const [waitlistStatus, setWaitlistStatus] = useState(null)

  async function handleWaitlistSubmit(e) {
    e.preventDefault()
    try {
      const res = await fetch('/api/waitlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: waitlistEmail }),
      })
      const data = await res.json()
      setWaitlistStatus(data.status === 'ok' ? 'success' : data.message || 'error')
    } catch {
      setWaitlistStatus('error')
    }
  }

  return (
    <div className="min-h-screen bg-white">
      {/* NAV */}
      <nav className="sticky top-0 z-50 border-b border-border bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link to="/" className="flex items-center gap-2 text-text-main hover:opacity-80">
            <LogoIcon />
            <span className="font-sora text-lg font-bold">StreetSignals</span>
          </Link>
          <div className="flex items-center gap-3">
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
      <section className="bg-gradient-to-b from-bg to-white px-6 pb-16 pt-20">
        <div className="mx-auto max-w-3xl text-center">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-4 py-1.5 text-sm font-medium text-primary">
            Free during beta
          </div>
          <h1 className="font-sora text-4xl font-bold leading-tight text-text-main md:text-5xl">
            Simple, transparent pricing
          </h1>
          <p className="mt-4 text-lg text-text-muted">
            StreetSignals is free while we're in beta. Paid plans are coming in Q3 2026.
          </p>
        </div>
      </section>

      {/* CARDS */}
      <section className="px-6 pb-24">
        <div className="mx-auto grid max-w-5xl gap-8 lg:grid-cols-3">

          {/* BETA (CURRENT) */}
          <div className="relative rounded-2xl border-2 border-primary bg-white p-8 shadow-lg">
            <div className="absolute -top-3 left-6 rounded-full bg-primary px-3 py-0.5 text-xs font-bold text-white">
              CURRENT
            </div>
            <h3 className="font-sora text-lg font-bold text-text-main">Beta</h3>
            <div className="mt-4 flex items-baseline gap-1">
              <span className="font-sora text-4xl font-bold text-text-main">$0</span>
              <span className="text-text-muted">/month</span>
            </div>
            <p className="mt-2 text-sm text-text-muted">Full access while we're building.</p>
            <Link
              to="/analyze"
              className="mt-6 block rounded-lg bg-primary px-4 py-2.5 text-center text-sm font-semibold text-white transition-colors hover:bg-primary-dark"
            >
              Start Analyzing&nbsp;&rarr;
            </Link>
            <ul className="mt-8 space-y-3 text-sm text-text-body">
              <li className="flex gap-2"><CheckIcon /> Unlimited script analyses</li>
              <li className="flex gap-2"><CheckIcon /> AI-powered rewrite suggestions</li>
              <li className="flex gap-2"><CheckIcon /> Negative interpretation detection</li>
              <li className="flex gap-2"><CheckIcon /> Bull/Bear defense analysis</li>
              <li className="flex gap-2"><CheckIcon /> Litigation &amp; activist risk flags</li>
              <li className="flex gap-2"><CheckIcon /> PDF, Word &amp; JSON exports</li>
              <li className="flex gap-2"><CheckIcon /> Analyst Q&amp;A prep</li>
            </ul>
          </div>

          {/* PRO (COMING SOON) */}
          <div className="rounded-2xl border border-border bg-white p-8">
            <h3 className="font-sora text-lg font-bold text-text-main">Pro</h3>
            <div className="mt-4 flex items-baseline gap-1">
              <span className="font-sora text-4xl font-bold text-text-main">TBD</span>
            </div>
            <p className="mt-2 text-sm text-text-muted">For IR teams running quarterly cycles.</p>
            <button
              onClick={() => { setShowWaitlist(true); setWaitlistStatus(null); setWaitlistEmail(''); }}
              className="mt-6 block w-full rounded-lg border border-border px-4 py-2.5 text-center text-sm font-semibold text-text-main transition-colors hover:border-primary hover:text-primary"
            >
              Get Notified
            </button>
            <ul className="mt-8 space-y-3 text-sm text-text-body">
              <li className="flex gap-2"><CheckIcon /> Everything in Beta</li>
              <li className="flex gap-2"><CheckIcon /> Historical score tracking</li>
              <li className="flex gap-2"><CheckIcon /> Quarter-over-quarter comparison</li>
              <li className="flex gap-2"><CheckIcon /> Team collaboration &amp; sharing</li>
              <li className="flex gap-2"><CheckIcon /> Priority analysis queue</li>
              <li className="flex gap-2"><CheckIcon /> Custom scoring profiles</li>
            </ul>
          </div>

          {/* ENTERPRISE (COMING SOON) */}
          <div className="rounded-2xl border border-border bg-white p-8">
            <h3 className="font-sora text-lg font-bold text-text-main">Enterprise</h3>
            <div className="mt-4 flex items-baseline gap-1">
              <span className="font-sora text-4xl font-bold text-text-main">Custom</span>
            </div>
            <p className="mt-2 text-sm text-text-muted">For agencies and large-cap IR teams.</p>
            <a
              href="mailto:hello@streetsignals.ai"
              className="mt-6 block rounded-lg border border-border px-4 py-2.5 text-center text-sm font-semibold text-text-main transition-colors hover:border-primary hover:text-primary"
            >
              Contact Us
            </a>
            <ul className="mt-8 space-y-3 text-sm text-text-body">
              <li className="flex gap-2"><CheckIcon /> Everything in Pro</li>
              <li className="flex gap-2"><CheckIcon /> SSO &amp; role-based access</li>
              <li className="flex gap-2"><CheckIcon /> API access</li>
              <li className="flex gap-2"><CheckIcon /> Dedicated support</li>
              <li className="flex gap-2"><CheckIcon /> On-prem deployment option</li>
              <li className="flex gap-2"><CheckIcon /> Custom integrations</li>
            </ul>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="border-t border-border bg-bg px-6 py-20">
        <div className="mx-auto max-w-3xl">
          <h2 className="text-center font-sora text-2xl font-bold text-text-main">Frequently asked questions</h2>
          <div className="mt-10 space-y-8">
            <div>
              <h3 className="font-sora font-semibold text-text-main">How long will the beta last?</h3>
              <p className="mt-2 text-sm leading-relaxed text-text-muted">
                We plan to introduce paid plans in Q3 2026. Beta users will get advance notice and early-adopter pricing.
              </p>
            </div>
            <div>
              <h3 className="font-sora font-semibold text-text-main">Will I lose access when pricing starts?</h3>
              <p className="mt-2 text-sm leading-relaxed text-text-muted">
                No. We'll give at least 30 days' notice before any changes. Beta users will always have a path to continue using StreetSignals.
              </p>
            </div>
            <div>
              <h3 className="font-sora font-semibold text-text-main">Is my data safe during the beta?</h3>
              <p className="mt-2 text-sm leading-relaxed text-text-muted">
                Yes. Your scripts are processed in memory and never stored. We don't use your content
                for AI training. See our <Link to="/privacy" className="text-primary underline">Privacy Policy</Link> for details.
              </p>
            </div>
            <div>
              <h3 className="font-sora font-semibold text-text-main">Are there any usage limits during beta?</h3>
              <p className="mt-2 text-sm leading-relaxed text-text-muted">
                Not currently. We reserve the right to introduce fair-use limits if needed, but for
                typical IR team usage there are no restrictions.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-border bg-white px-6 py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 sm:flex-row">
          <Link to="/" className="flex items-center gap-2">
            <LogoIcon />
            <span className="font-sora text-sm font-bold text-text-main">StreetSignals</span>
          </Link>
          <div className="flex items-center gap-6 text-sm text-text-muted">
            <span className="font-medium text-text-main">Pricing</span>
            <Link to="/terms" className="hover:text-primary">Terms</Link>
            <Link to="/privacy" className="hover:text-primary">Privacy</Link>
          </div>
          <p className="text-sm text-text-muted">&copy; 2026 StreetSignals.ai</p>
        </div>
      </footer>

      {/* WAITLIST MODAL */}
      {showWaitlist && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={() => setShowWaitlist(false)}>
          <div className="mx-4 w-full max-w-md rounded-2xl bg-white p-8 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-sora text-xl font-bold text-text-main">Get notified when Pro launches</h3>
            <p className="mt-2 text-sm text-text-muted">We'll email you when paid plans are available — plus early-adopter pricing.</p>
            {waitlistStatus === 'success' ? (
              <div className="mt-6 rounded-lg bg-green-50 p-4 text-center text-sm font-medium text-green-700">
                You're on the list! We'll be in touch.
              </div>
            ) : (
              <form onSubmit={handleWaitlistSubmit} className="mt-6">
                <input
                  type="email"
                  required
                  value={waitlistEmail}
                  onChange={(e) => setWaitlistEmail(e.target.value)}
                  placeholder="you@company.com"
                  className="w-full rounded-lg border border-border px-4 py-2.5 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
                <button
                  type="submit"
                  className="mt-3 w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-dark"
                >
                  Notify Me
                </button>
                {waitlistStatus === 'error' && (
                  <p className="mt-2 text-center text-xs text-red-500">Something went wrong. Try again.</p>
                )}
              </form>
            )}
            <button onClick={() => setShowWaitlist(false)} className="mt-4 w-full text-center text-sm text-text-muted hover:text-text-main">
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
