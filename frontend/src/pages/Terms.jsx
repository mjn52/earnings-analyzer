import { Link } from 'react-router-dom'

export default function Terms() {
  return (
    <div className="min-h-screen bg-white">
      {/* NAV */}
      <nav className="border-b border-border px-6 py-4">
        <div className="mx-auto flex max-w-4xl items-center gap-3">
          <Link to="/" className="flex items-center gap-2 text-text-main hover:opacity-80">
            <svg viewBox="0 0 28 28" fill="none" className="h-7 w-7" aria-hidden="true">
              <rect x="2" y="16" width="4" height="10" rx="1" fill="#1A56DB" />
              <rect x="8" y="10" width="4" height="16" rx="1" fill="#1A56DB" opacity="0.8" />
              <rect x="14" y="6" width="4" height="20" rx="1" fill="#1A56DB" opacity="0.6" />
              <rect x="20" y="2" width="4" height="24" rx="1" fill="#1A56DB" opacity="0.4" />
            </svg>
            <span className="font-sora text-lg font-bold">StreetSignals</span>
          </Link>
        </div>
      </nav>

      {/* CONTENT */}
      <main className="mx-auto max-w-4xl px-6 py-12">
        <h1 className="font-sora text-3xl font-bold text-text-main">Terms of Use</h1>
        <p className="mt-2 text-sm text-text-muted">Effective Date: April 2, 2026</p>

        <div className="prose prose-gray mt-8 max-w-none text-text-body [&_h2]:font-sora [&_h2]:text-xl [&_h2]:font-semibold [&_h2]:text-text-main [&_h2]:mt-10 [&_h2]:mb-3 [&_p]:leading-relaxed [&_p]:mb-4 [&_ul]:mb-4 [&_ul]:list-disc [&_ul]:pl-6 [&_li]:mb-1">

          <h2>1. Acceptance of Terms</h2>
          <p>
            By accessing or using StreetSignals.ai (the "Service"), you agree to be bound by these
            Terms of Use. If you do not agree, do not use the Service. We may update these Terms at
            any time; continued use after changes constitutes acceptance.
          </p>

          <h2>2. Description of Service</h2>
          <p>
            StreetSignals.ai is an AI-powered earnings script analyzer that evaluates language risk,
            sentiment, hedging, and other linguistic patterns in corporate earnings call scripts.
            The Service provides suggested rewrites, risk annotations, and analytical scores to help
            investor relations teams prepare stronger communications.
          </p>

          <h2>3. Eligibility</h2>
          <p>
            The Service is intended for use by business professionals. By using the Service, you
            represent that you are at least 18 years old and have the authority to agree to these
            Terms on behalf of yourself or the organization you represent.
          </p>

          <h2>4. Acceptable Use</h2>
          <p>You agree not to:</p>
          <ul>
            <li>Use the Service for any unlawful purpose or to facilitate securities fraud, market manipulation, or insider trading.</li>
            <li>Upload content that you do not have the right to share or that contains material non-public information (MNPI) that you are legally prohibited from disclosing.</li>
            <li>Attempt to reverse-engineer, decompile, or extract the underlying models, algorithms, or scoring methodologies.</li>
            <li>Use automated scripts, bots, or scrapers to access the Service beyond normal usage.</li>
            <li>Interfere with or disrupt the Service's infrastructure or security.</li>
          </ul>

          <h2>5. Your Content</h2>
          <p>
            You retain full ownership of all scripts, transcripts, and other content you upload to
            the Service ("Your Content"). By uploading Your Content, you grant StreetSignals.ai a
            limited, temporary license to process it solely for the purpose of providing analysis
            results to you during your session.
          </p>
          <p>
            Your Content is processed in memory and is not persisted to disk or any database after
            your session ends. We do not use Your Content to train AI models.
          </p>

          <h2>6. Disclaimer — Not Financial or Legal Advice</h2>
          <p>
            The Service provides linguistic analysis and suggested rewrites for informational
            purposes only. Nothing produced by StreetSignals.ai constitutes financial advice,
            investment advice, legal advice, or a recommendation to buy, sell, or hold any security.
          </p>
          <p>
            AI-generated analysis may contain errors, hallucinations, or inappropriate suggestions.
            You are solely responsible for reviewing all output and making your own decisions about
            whether and how to use it. Always consult qualified legal and financial advisors before
            making disclosure decisions.
          </p>

          <h2>7. Intellectual Property</h2>
          <p>
            All rights in the Service — including its design, scoring algorithms, analysis
            methodologies, branding, and software — are owned by StreetSignals.ai. These Terms do
            not grant you any rights to our intellectual property except the limited right to use
            the Service as described herein.
          </p>

          <h2>8. Third-Party Services</h2>
          <p>
            The Service uses third-party APIs to perform analysis (including Anthropic's Claude for
            AI-powered rewrites and Financial Modeling Prep for market data). Your use of the
            Service is also subject to those providers' terms. We are not responsible for the
            availability or accuracy of third-party services.
          </p>

          <h2>9. Limitation of Liability</h2>
          <p>
            TO THE MAXIMUM EXTENT PERMITTED BY LAW, STREETSIGNALS.AI AND ITS OFFICERS, DIRECTORS,
            EMPLOYEES, AND AGENTS SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL,
            CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR ANY LOSS OF PROFITS, REVENUE, DATA, OR
            GOODWILL, ARISING FROM OR RELATED TO YOUR USE OF THE SERVICE.
          </p>
          <p>
            OUR TOTAL AGGREGATE LIABILITY FOR ANY CLAIMS ARISING FROM THESE TERMS OR YOUR USE OF
            THE SERVICE SHALL NOT EXCEED THE AMOUNT YOU PAID US IN THE TWELVE (12) MONTHS PRECEDING
            THE CLAIM, OR ONE HUNDRED DOLLARS ($100), WHICHEVER IS GREATER.
          </p>

          <h2>10. Indemnification</h2>
          <p>
            You agree to indemnify and hold harmless StreetSignals.ai from any claims, damages,
            losses, or expenses (including reasonable attorneys' fees) arising from your use of the
            Service, your violation of these Terms, or your violation of any third party's rights.
          </p>

          <h2>11. Termination</h2>
          <p>
            We may suspend or terminate your access to the Service at any time, for any reason,
            without notice. Upon termination, your right to use the Service ceases immediately.
            Sections 6, 9, 10, and 12 survive termination.
          </p>

          <h2>12. Governing Law</h2>
          <p>
            These Terms are governed by the laws of the State of Delaware, without regard to
            conflict of law principles. Any disputes shall be resolved in the state or federal
            courts located in Delaware.
          </p>

          <h2>13. Contact</h2>
          <p>
            Questions about these Terms? Contact us at{' '}
            <a href="mailto:legal@streetsignals.ai" className="text-primary underline">legal@streetsignals.ai</a>.
          </p>
        </div>
      </main>

      {/* FOOTER */}
      <footer className="border-t border-border bg-white px-6 py-8">
        <div className="mx-auto flex max-w-4xl flex-col items-center justify-between gap-4 sm:flex-row">
          <Link to="/" className="flex items-center gap-2">
            <svg viewBox="0 0 28 28" fill="none" className="h-6 w-6" aria-hidden="true">
              <rect x="2" y="16" width="4" height="10" rx="1" fill="#1A56DB" />
              <rect x="8" y="10" width="4" height="16" rx="1" fill="#1A56DB" opacity="0.8" />
              <rect x="14" y="6" width="4" height="20" rx="1" fill="#1A56DB" opacity="0.6" />
              <rect x="20" y="2" width="4" height="24" rx="1" fill="#1A56DB" opacity="0.4" />
            </svg>
            <span className="font-sora text-sm font-bold text-text-main">StreetSignals</span>
          </Link>
          <div className="flex items-center gap-6 text-sm text-text-muted">
            <span className="font-medium text-text-main">Terms</span>
            <Link to="/privacy" className="hover:text-primary">Privacy</Link>
          </div>
          <p className="text-sm text-text-muted">&copy; 2026 StreetSignals.ai</p>
        </div>
      </footer>
    </div>
  )
}
