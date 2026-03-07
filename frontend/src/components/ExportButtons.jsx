function DownloadIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
    </svg>
  )
}

export default function ExportButtons({ sessionId }) {
  if (!sessionId) return null

  const buttons = [
    { label: 'PDF', path: `/api/export/pdf/${sessionId}` },
    { label: 'Word', path: `/api/export/word/${sessionId}` },
    { label: 'JSON', path: `/api/export/json/${sessionId}` },
  ]

  return (
    <div className="flex items-center gap-2">
      {buttons.map((btn) => (
        <a
          key={btn.label}
          href={btn.path}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-white px-3 py-1.5 text-xs font-medium text-text-main transition-colors hover:border-primary hover:text-primary"
        >
          <DownloadIcon />
          {btn.label}
        </a>
      ))}
    </div>
  )
}
