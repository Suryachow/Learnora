import { api } from './client'

export function register(payload) {
  return api.post('/auth/register', payload, { auth: false })
}

export function login(payload) {
  return api.post('/auth/login', payload, { auth: false })
}

export function fetchMe() {
  return api.get('/me')
}

export function updateMe(payload) {
  return api.patch('/me', payload)
}
