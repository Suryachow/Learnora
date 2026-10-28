import { formatPaise, formatRupees } from '../utils/money'

/**
 * Money is always shown with this component so gold stays reserved for
 * balances, earnings and reward amounts.
 */
export function Amount({ paise, label, compact = false, className = '' }) {
  return (
    <span className={`amount-chip ${className}`.trim()}>
      {label ? <span className="amount-chip__label">{label}</span> : null}
      <span className="amount">{compact ? formatRupees(paise) : formatPaise(paise)}</span>
    </span>
  )
}

export default Amount
