/**
 * Every amount in the API is an integer number of paise (₹1 = 100 paise).
 * Formatting happens here and nowhere else, so amounts never drift into floats.
 */
const rupees = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

/** "₹149.00" - the exact amount, used for balances and ledger rows. */
export function formatPaise(paise) {
  const value = Number(paise)
  return rupees.format((Number.isFinite(value) ? value : 0) / 100)
}

/** "₹2,500" - drops the (usually zero) paise, used on reward chips and cards. */
export function formatRupees(paise) {
  const value = Math.round((Number(paise) || 0) / 100)
  return `₹${value.toLocaleString('en-IN')}`
}

/** Ledger rows are signed; show rewards with a leading plus sign. */
export function formatSignedPaise(paise) {
  const value = Number(paise) || 0
  return `${value > 0 ? '+' : value < 0 ? '−' : ''}${formatPaise(Math.abs(value))}`
}
