import { useEffect, useRef } from 'react'

function scoreColor(score) {
  if (score >= 75) return '#059669'
  if (score >= 50) return '#D97706'
  return '#DC2626'
}

export default function ScoreRing({ score, grade, size = 180, strokeWidth = 10 }) {
  const circleRef = useRef(null)
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference
  const color = scoreColor(score)

  useEffect(() => {
    const el = circleRef.current
    if (!el) return
    el.style.strokeDashoffset = circumference
    // Force reflow
    el.getBoundingClientRect()
    el.style.transition = 'stroke-dashoffset 0.6s ease-out'
    el.style.strokeDashoffset = offset
  }, [score, circumference, offset])

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#E4E8F0"
          strokeWidth={strokeWidth}
        />
        <circle
          ref={circleRef}
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference}
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center" style={{ width: size, height: size }}>
        <span className="font-mono text-4xl font-bold" style={{ color }}>{score}</span>
        <span className="text-sm text-text-muted">/100</span>
      </div>
      <p className="mt-3 font-sora text-2xl font-bold" style={{ color }}>
        {grade}
      </p>
    </div>
  )
}
