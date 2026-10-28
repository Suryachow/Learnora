import { api } from './client'

/** Every call here needs an admin token; the server answers 403 otherwise. */

// --- Reports ---------------------------------------------------------------

export function fetchOverview() {
  return api.get('/admin/reports/overview')
}

// --- Catalogue: courses ----------------------------------------------------

export function fetchCourses(search) {
  const query = search ? `?search=${encodeURIComponent(search)}` : ''
  return api.get(`/admin/courses${query}`)
}

export function createCourse(payload) {
  return api.post('/admin/courses', payload)
}

export function updateCourse(courseId, changes) {
  return api.patch(`/admin/courses/${courseId}`, changes)
}

export function deleteCourse(courseId) {
  return api.delete(`/admin/courses/${courseId}`)
}

// --- Catalogue: topics -----------------------------------------------------

export function fetchTopics(courseId) {
  return api.get(`/admin/courses/${courseId}/topics`)
}

export function createTopic(courseId, payload) {
  return api.post(`/admin/courses/${courseId}/topics`, payload)
}

export function updateTopic(topicId, changes) {
  return api.patch(`/admin/topics/${topicId}`, changes)
}

export function deleteTopic(topicId) {
  return api.delete(`/admin/topics/${topicId}`)
}

export function reorderTopics(courseId, orderedIds) {
  return api.post(`/admin/courses/${courseId}/topics/reorder`, { ordered_ids: orderedIds })
}

// --- Tasks / quiz builder --------------------------------------------------

export function fetchTasks({ search, topicId, courseId } = {}) {
  const params = new URLSearchParams()
  if (search) params.set('search', search)
  if (topicId) params.set('topic_id', topicId)
  if (courseId) params.set('course_id', courseId)
  const query = params.toString()
  return api.get(`/admin/tasks${query ? `?${query}` : ''}`)
}

export function fetchTask(taskId) {
  return api.get(`/admin/tasks/${taskId}`)
}

export function createTask(payload) {
  return api.post('/admin/tasks', payload)
}

export function updateTask(taskId, changes) {
  return api.patch(`/admin/tasks/${taskId}`, changes)
}

export function deleteTask(taskId) {
  return api.delete(`/admin/tasks/${taskId}`)
}

// --- Users -----------------------------------------------------------------

export function fetchUsers({ search, limit = 25, offset = 0 } = {}) {
  const params = new URLSearchParams({ limit, offset })
  if (search) params.set('search', search)
  return api.get(`/admin/users?${params.toString()}`)
}

export function updateUser(userId, changes) {
  return api.patch(`/admin/users/${userId}`, changes)
}

// --- Runtime settings ------------------------------------------------------

export function fetchSettings() {
  return api.get('/admin/settings')
}

export function updateSettings(values) {
  return api.patch('/admin/settings', { values })
}

export function resetSetting(key) {
  return api.post(`/admin/settings/${key}/reset`)
}
