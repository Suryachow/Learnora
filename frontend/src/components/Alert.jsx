/**
 * One consistent way to show problems and confirmations.
 * `error` alerts are announced to screen readers immediately.
 */
export function Alert({ tone = 'error', children }) {
  if (!children) return null
  return (
    <div className={`alert alert--${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      {children}
    </div>
  )
}

export default Alert
