import { api } from './client'

/** The questions. The answers stay on the server and are never included. */
export function fetchQuiz(taskId) {
  return api.get(`/tasks/${taskId}/quiz`)
}

/** `answers` maps a question id to the index of the chosen option. */
export function submitAttempt(taskId, answers) {
  return api.post(`/tasks/${taskId}/attempts`, { answers })
}

export function fetchMyAttempts({ limit = 20, offset = 0 } = {}) {
  const params = new URLSearchParams({ limit, offset })
  return api.get(`/me/attempts?${params.toString()}`)
}
