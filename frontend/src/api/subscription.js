import { api } from './client'

export function fetchPlan() {
  return api.get('/subscription/plan', { auth: false })
}

/** Creates a payment order. This does NOT activate anything on its own. */
export function createCheckout() {
  return api.post('/subscription/checkout')
}

/**
 * Development only. Stands in for the payment gateway and still goes through
 * the server's signature check, so the real webhook path stays exercised.
 */
export function simulatePayment(orderId) {
  return api.post('/subscription/dev/simulate-payment', { order_id: orderId })
}
