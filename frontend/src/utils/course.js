/** Course detail shared by the catalogue cards and the course page. */

export const LEVEL_LABELS = {
  beginner: 'Beginner',
  intermediate: 'Intermediate',
  advanced: 'Advanced',
}

export const LEVEL_OPTIONS = Object.entries(LEVEL_LABELS).map(([value, label]) => ({
  value,
  label,
}))

/** "45 min", "2h", "2h 30m" - empty when the admin left the duration blank. */
export function formatDuration(minutes) {
  const total = Number(minutes)
  if (!total || total <= 0) return ''
  const hours = Math.floor(total / 60)
  const rest = total % 60
  if (!hours) return `${rest} min`
  return rest ? `${hours}h ${rest}m` : `${hours}h`
}
