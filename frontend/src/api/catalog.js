import { api } from './client'

/** Courses, topics and tasks are readable without an account. */
export function fetchCategories() {
  return api.get('/categories', { auth: false })
}

export function fetchCourses({ category, search } = {}) {
  const params = new URLSearchParams()
  if (category) params.set('category', category)
  if (search) params.set('search', search)
  const query = params.toString()
  return api.get(`/courses${query ? `?${query}` : ''}`, { auth: false })
}

/**
 * Public, but the token is sent when there is one: a signed-in reader needs to
 * know whether they already own a paid course.
 */
export function fetchCourse(courseId) {
  return api.get(`/courses/${courseId}`)
}

/**
 * Public, but the token is sent when there is one so a signed-in reader sees
 * their own progress through the lesson.
 */
export function fetchTopic(topicId) {
  return api.get(`/topics/${topicId}`)
}

/** Task detail needs a signed-in user, and never includes the answers. */
export function fetchTask(taskId) {
  return api.get(`/tasks/${taskId}`)
}

/**
 * Start a payment for one course. The server prices it from the catalogue and
 * returns the order; nothing is unlocked until the provider confirms it.
 */
export function createCourseCheckout(courseId) {
  return api.post(`/courses/${courseId}/checkout`)
}

/**
 * Development only: stand in for the gateway confirming the payment. The server
 * signs the callback itself, so the same verification runs as in production.
 */
export function simulateCoursePayment(courseId, orderId) {
  return api.post(`/courses/${courseId}/dev/simulate-payment`, { order_id: orderId })
}

/** The courses this learner has already unlocked. */
export function fetchMyCourses() {
  return api.get('/me/courses')
}
