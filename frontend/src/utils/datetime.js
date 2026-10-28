/**
 * Timestamps arrive from the API as naive UTC ("2026-10-17T13:00:00"), so they
 * must be tagged as UTC before the browser parses them.
 */
export function parseUtc(value) {
  if (!value) return null
  const hasTimezone = /(Z|[+-]\d{2}:?\d{2})$/.test(value)
  const date = new Date(hasTimezone ? value : `${value}Z`)
  return Number.isNaN(date.getTime()) ? null : date
}

export function formatDate(value) {
  const date = parseUtc(value)
  if (!date) return '—'
  return date.toLocaleDateString(undefined, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function formatDateTime(value) {
  const date = parseUtc(value)
  if (!date) return '—'
  return date.toLocaleString(undefined, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}
