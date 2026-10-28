/** A thin progress bar. `tone="gold"` is reserved for money progress. */
export function ProgressBar({ value, max = 100, tone = 'primary', label }) {
  const safeMax = max > 0 ? max : 100
  const percent = Math.max(0, Math.min(100, Math.round((value / safeMax) * 100)))

  return (
    <div
      className="progress"
      role="progressbar"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={safeMax}
      aria-label={label}
    >
      <div
        className={`progress__bar ${tone === 'gold' ? 'progress__bar--gold' : ''}`.trim()}
        style={{ width: `${percent}%` }}
      />
    </div>
  )
}

export default ProgressBar
