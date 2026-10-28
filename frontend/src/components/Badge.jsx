/**
 * Small status label. `tone` picks the colour; it is never used for money,
 * which keeps gold meaning "reward" everywhere.
 */
export function Badge({ tone = 'neutral', children }) {
  return <span className={`badge badge--${tone}`}>{children}</span>
}

export default Badge
