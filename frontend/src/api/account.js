import { api } from './client'

export function changePassword(payload) {
  return api.post('/me/password', payload)
}

export function fetchPreferences() {
  return api.get('/me/preferences')
}

export function updatePreferences(changes) {
  return api.patch('/me/preferences', changes)
}

export function fetchBilling({ limit = 20, offset = 0 } = {}) {
  const params = new URLSearchParams({ limit, offset })
  return api.get(`/me/billing?${params.toString()}`)
}
