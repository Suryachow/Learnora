/** Grey shimmer shown while a page loads, so layout does not jump. */
export function Skeleton({ height = 16, width = '100%', className = '' }) {
  return (
    <span
      className={`skeleton ${className}`.trim()}
      style={{ height, width, display: 'block' }}
      aria-hidden="true"
    />
  )
}

export function SkeletonList({ rows = 3, height = 16 }) {
  return (
    <div className="stack" aria-hidden="true">
      {Array.from({ length: rows }, (_value, index) => (
        <Skeleton key={index} height={height} />
      ))}
    </div>
  )
}

export default Skeleton
