import { api } from './client'

/**
 * Video completion and the understanding check.
 *
 * The browser reports what it watched; the server decides whether that counts
 * as "watched in full" before it records anything.
 */
export function completeVideo(topicId, { watchedSeconds, durationSeconds }) {
  return api.post(`/topics/${topicId}/video-complete`, {
    watched_seconds: watchedSeconds,
    duration_seconds: durationSeconds,
  })
}

export function saveUnderstanding(topicId, { rating, note }) {
  return api.post(`/topics/${topicId}/understanding`, { rating, note })
}

export function fetchMyProgress() {
  return api.get('/me/progress')
}
