import { api } from './client'

/**
 * The balance is computed by the server from the ledger; the client only shows
 * what it is told. `kind` can be 'subscription' | 'reward' | 'withdrawal'
 * | 'course_purchase' (paid from the balance) | 'course_payment' (paid by card).
 */
export function fetchWallet({ limit = 20, offset = 0, kind } = {}) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  if (kind) params.set('kind', kind)
  return api.get(`/wallet?${params.toString()}`)
}
