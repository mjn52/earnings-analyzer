import { Link } from 'react-router-dom'

export default function Privacy() {
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
        <h1 className="font-sora text-3xl font-bold text-text-main">Privacy Policy</h1>
        <p className="mt-2 text-sm text-text-muted">Effective Date: April 2, 2026</p>

        <div className="prose prose-gray mt-8 max-w-none text-text-body [&_h2]:font-sora [&_h2]:text-xl [&_h2]:font-semibold [&_h2]:text-text-main [&_h2]:mt-10 [&_h2]:mb-3 [&_p]:leading-relaxed [&_p]:mb-4 [&_ul]:mb-4 [&_ul]:list-disc [&_ul]:pl-6 [&_li]:mb-1 [&_table]:w-full [&_table]:text-sm [&_th]:text-left [&_th]:pb-2 [&_th]:pr-4 [&_th]:font-semibold [&_td]:py-2 [&_td]:pr-4 [&_td]:align-top">

          <h2>1. Overview</h2>
          <p>
            StreetSignals.ai ("we", "us", "our") respects your privacy. This Privacy Policy
            explains what information we collect, how we use it, and the choices you have. We are
            committed to minimizing data collection and never selling your information.
          </p>

          <h2>2. Information We Collect</h2>

          <p><strong>Information you provide directly:</strong></p>
          <table>
            <thead>
              <tr>
                <th>Data</th>
                <th>When</th>
                <th>Retention</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Email address</td>
                <td>When you join the early-access waitlist</td>
                <td>Until you request removal</td>
              </tr>
              <tr>
                <td>Earnings script text</td>
                <td>When you upload or paste a transcript for analysis</td>
                <td>In-memory only during your session; never written to disk or a database</td>
              </tr>
              <tr>
                <td>Company ticker (optional)</td>
                <td>When you provide it alongside a transcript</td>
                <td>In-memory only during your session</td>
              </tr>
            </tbody>
          </table>

          <p><strong>Information we do NOT collect:</strong></p>
          <ul>
            <li>We do not use cookies, web beacons, or pixel trackers.</li>
            <li>We do not run third-party analytics (no Google Analytics, Segment, Mixpanel, etc.).</li>
            <li>We do not collect device fingerprints or persistent identifiers.</li>
            <li>We do not create user accounts or store passwords (as of the current version).</li>
          </ul>

          <h2>3. How We Use Your Information</h2>
          <ul>
            <li><strong>Transcript analysis:</strong> Your uploaded text is sent to our backend and processed using local algorithms and third-party AI APIs to generate linguistic risk scores, suggested rewrites, and other analysis. The text exists only in server memory for the duration of your session.</li>
            <li><strong>Waitlist communications:</strong> Your email address is used solely to notify you about early access availability and product updates. We will not send unsolicited marketing.</li>
            <li><strong>Service improvement:</strong> We may collect aggregate, anonymized usage metrics (e.g., total number of analyses run) to improve the Service. These metrics cannot be traced back to any individual or uploaded content.</li>
          </ul>

          <h2>4. Third-Party Data Processors</h2>
          <p>
            To provide the Service, your transcript text is shared with the following third-party
            API providers during analysis:
          </p>
          <table>
            <thead>
              <tr>
                <th>Provider</th>
                <th>Purpose</th>
                <th>Their Privacy Policy</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Anthropic (Claude API)</td>
                <td>AI-powered rewrite suggestions, Q&A generation, and advanced analysis</td>
                <td><a href="https://www.anthropic.com/privacy" className="text-primary underline" target="_blank" rel="noopener noreferrer">anthropic.com/privacy</a></td>
              </tr>
              <tr>
                <td>Financial Modeling Prep</td>
                <td>Market data, consensus estimates, and peer comparisons (ticker-based lookups only; your transcript is not sent to FMP)</td>
                <td><a href="https://financialmodelingprep.com/developer/docs/terms" className="text-primary underline" target="_blank" rel="noopener noreferrer">financialmodelingprep.com</a></td>
              </tr>
            </tbody>
          </table>
          <p>
            We use Anthropic's API with the understanding that data sent via the API is not used to
            train their models. We do not send your transcript to any other third party.
          </p>

          <h2>5. Data Retention &amp; Deletion</h2>
          <ul>
            <li><strong>Transcripts and analysis results</strong> are held in server memory only. They are automatically discarded when your session ends or the server restarts. We do not write your content to any persistent storage.</li>
            <li><strong>Exported files</strong> (PDF, Word, JSON) are generated as temporary files, delivered to your browser, and not retained on our servers.</li>
            <li><strong>Waitlist emails</strong> are stored in a local file on our server. To request removal, email us at <a href="mailto:privacy@streetsignals.ai" className="text-primary underline">privacy@streetsignals.ai</a>.</li>
          </ul>

          <h2>6. Data Security</h2>
          <p>
            We implement reasonable technical safeguards to protect your data, including:
          </p>
          <ul>
            <li>All data in transit is encrypted via HTTPS/TLS.</li>
            <li>API keys for third-party services are stored as server-side environment variables and never exposed to the browser.</li>
            <li>No persistent database means there is no stored data to breach.</li>
          </ul>
          <p>
            However, no system is 100% secure. You acknowledge that you upload content at your own
            risk and should not upload material non-public information (MNPI) or other highly
            sensitive data unless you are comfortable with the inherent risks of internet
            transmission.
          </p>

          <h2>7. Children's Privacy</h2>
          <p>
            The Service is not directed at individuals under 18 years of age. We do not knowingly
            collect personal information from children. If you believe a child has provided us with
            personal information, please contact us and we will promptly delete it.
          </p>

          <h2>8. Your Rights</h2>
          <p>Depending on your jurisdiction, you may have the right to:</p>
          <ul>
            <li><strong>Access</strong> the personal data we hold about you.</li>
            <li><strong>Delete</strong> your personal data (e.g., your waitlist email).</li>
            <li><strong>Object</strong> to or restrict certain processing.</li>
            <li><strong>Data portability</strong> — receive your data in a structured format.</li>
          </ul>
          <p>
            Since we retain minimal data (only waitlist emails), most of these rights can be
            exercised by simply emailing{' '}
            <a href="mailto:privacy@streetsignals.ai" className="text-primary underline">privacy@streetsignals.ai</a>.
          </p>

          <h2>9. California Residents (CCPA)</h2>
          <p>
            If you are a California resident, you have the right to know what personal information
            we collect and to request its deletion. We do not sell personal information. To exercise
            your rights, contact us at the email below.
          </p>

          <h2>10. International Users</h2>
          <p>
            The Service is operated from the United States. If you are accessing the Service from
            outside the US, your information may be transferred to and processed in the US. By
            using the Service, you consent to this transfer.
          </p>

          <h2>11. Changes to This Policy</h2>
          <p>
            We may update this Privacy Policy from time to time. We will post the revised version
            on this page with an updated effective date. Material changes will be communicated via
            the Service or by email to waitlist subscribers.
          </p>

          <h2>12. Contact Us</h2>
          <p>
            For privacy-related questions or requests, contact us at{' '}
            <a href="mailto:privacy@streetsignals.ai" className="text-primary underline">privacy@streetsignals.ai</a>.
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
            <Link to="/terms" className="hover:text-primary">Terms</Link>
            <span className="font-medium text-text-main">Privacy</span>
          </div>
          <p className="text-sm text-text-muted">&copy; 2026 StreetSignals.ai</p>
        </div>
      </footer>
    </div>
  )
}
