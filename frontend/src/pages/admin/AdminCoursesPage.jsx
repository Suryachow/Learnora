import { useCallback, useState } from 'react'

import {
  createCourse,
  createTopic,
  deleteCourse,
  deleteTopic,
  fetchCourses,
  fetchTopics,
  reorderTopics,
  updateCourse,
  updateTopic,
} from '../../api/admin'
import Amount from '../../components/Amount'
import Alert from '../../components/Alert'
import Badge from '../../components/Badge'
import Button from '../../components/Button'
import FormField from '../../components/FormField'
import Modal from '../../components/Modal'
import Switch from '../../components/Switch'
import { Loading } from '../../components/Spinner'
import useFetch from '../../hooks/useFetch'
import { LEVEL_OPTIONS } from '../../utils/course'

const EMPTY_COURSE = {
  title: '',
  category: '',
  description: '',
  is_published: false,
  price_rupees: '',
  cover_image_url: '',
  level: 'beginner',
  duration_minutes: '',
  outcomes_text: '',
  access_days: '',
}
const EMPTY_TOPIC = { title: '', video_url: '', content: '' }

/** Blank numbers mean "not set" rather than zero. */
function numberOrNull(value) {
  return value === '' || value === null ? null : Number(value)
}

function outcomeLines(values) {
  return values.outcomes_text
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
}

/** The form edits rupees; the API only ever sees integer paise. */
function coursePayload(values) {
  return {
    title: values.title,
    category: values.category,
    description: values.description,
    is_published: values.is_published,
    price_paise: Math.round(Number(values.price_rupees || 0) * 100),
    cover_image_url: values.cover_image_url.trim(),
    level: values.level,
    duration_minutes: numberOrNull(values.duration_minutes),
    outcomes: outcomeLines(values),
    access_days: numberOrNull(values.access_days),
  }
}

function courseToForm(course) {
  return {
    title: course.title,
    category: course.category,
    description: course.description,
    is_published: course.is_published,
    price_rupees: course.price_paise ? String(course.price_paise / 100) : '',
    cover_image_url: course.cover_image_url ?? '',
    level: course.level ?? 'beginner',
    duration_minutes: course.duration_minutes ?? '',
    outcomes_text: (course.outcomes ?? []).join('\n'),
    access_days: course.access_days ?? '',
  }
}

function move(list, index, delta) {
  const target = index + delta
  if (target < 0 || target >= list.length) return list
  const next = [...list]
  ;[next[index], next[target]] = [next[target], next[index]]
  return next
}

/** Courses, their topics, and the order topics appear in. */
export function AdminCoursesPage() {
  const [search, setSearch] = useState('')
  const [query, setQuery] = useState('')
  const [selectedCourse, setSelectedCourse] = useState(null)
  const [courseForm, setCourseForm] = useState(null)
  const [topicForm, setTopicForm] = useState(null)
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const [notice, setNotice] = useState('')

  /** Functional update: the form has many fields and one handler. */
  function setCourseValue(field, value) {
    setCourseForm((current) => ({ ...current, values: { ...current.values, [field]: value } }))
  }

  const loadCourses = useCallback(() => fetchCourses(query || undefined), [query])
  const { data: courses, loading, error, reload } = useFetch(loadCourses)

  const loadTopics = useCallback(
    () => (selectedCourse ? fetchTopics(selectedCourse.id) : Promise.resolve(null)),
    [selectedCourse],
  )
  const { data: topics, setData: setTopics } = useFetch(loadTopics)

  async function run(action, message) {
    setBusy(true)
    setProblem('')
    setNotice('')
    try {
      await action()
      if (message) setNotice(message)
      return true
    } catch (err) {
      setProblem(err.message)
      return false
    } finally {
      setBusy(false)
    }
  }

  async function saveCourse(event) {
    event.preventDefault()
    const values = coursePayload(courseForm.values)
    const ok = await run(async () => {
      if (courseForm.mode === 'create') {
        await createCourse(values)
      } else {
        await updateCourse(courseForm.id, values)
      }
      reload()
    }, courseForm.mode === 'create' ? 'Course created.' : 'Course updated.')

    if (ok) setCourseForm(null)
  }

  async function removeCourse(course) {
    if (!window.confirm(`Delete “${course.title}” with all its topics and tasks?`)) return
    await run(async () => {
      await deleteCourse(course.id)
      if (selectedCourse?.id === course.id) setSelectedCourse(null)
      reload()
    }, 'Course deleted.')
  }

  async function saveTopic(event) {
    event.preventDefault()
    const values = { ...topicForm.values }
    if (!values.video_url) delete values.video_url

    const ok = await run(async () => {
      if (topicForm.mode === 'create') {
        await createTopic(selectedCourse.id, values)
      } else {
        await updateTopic(topicForm.id, values)
      }
      setTopics(await fetchTopics(selectedCourse.id))
      reload()
    }, topicForm.mode === 'create' ? 'Topic added.' : 'Topic updated.')

    if (ok) setTopicForm(null)
  }

  async function removeTopic(topic) {
    if (!window.confirm(`Delete “${topic.title}” and its tasks?`)) return
    await run(async () => {
      await deleteTopic(topic.id)
      setTopics(await fetchTopics(selectedCourse.id))
      reload()
    }, 'Topic deleted.')
  }

  async function shift(index, delta) {
    const reordered = move(topics, index, delta)
    if (reordered === topics) return
    await run(async () => {
      setTopics(await reorderTopics(selectedCourse.id, reordered.map((topic) => topic.id)))
    })
  }

  return (
    <div className="stack">
      <header className="page-header">
        <h1>Courses and topics</h1>
        <p>Create the catalogue, publish it, and keep the topic order the way learners read it.</p>
      </header>

      <Alert>{problem}</Alert>
      <Alert tone="success">{notice}</Alert>

      <div className="toolbar">
        <form
          className="toolbar__actions"
          onSubmit={(event) => {
            event.preventDefault()
            setQuery(search.trim())
          }}
        >
          <input
            className="field__input"
            type="search"
            aria-label="Search courses"
            placeholder="Search courses"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <Button type="submit" variant="secondary">
            Search
          </Button>
        </form>
        <div className="toolbar__actions">
          <Button onClick={() => setCourseForm({ mode: 'create', values: EMPTY_COURSE })}>
            New course
          </Button>
        </div>
      </div>

      {loading ? <Loading label="Loading the catalogue…" /> : null}

      {error ? (
        <div className="stack">
          <Alert>{error.message}</Alert>
          <button type="button" className="btn btn--secondary" onClick={reload}>
            Try again
          </button>
        </div>
      ) : null}

      {courses ? (
        <section className="card">
          <h2 className="card__title">
            {courses.length} course{courses.length === 1 ? '' : 's'}
          </h2>

          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">Course</th>
                  <th scope="col">Price</th>
                  <th scope="col">Status</th>
                  <th scope="col">Topics</th>
                  <th scope="col">Tasks</th>
                  <th scope="col">Rewards offered</th>
                  <th scope="col">Buyers</th>
                  <th scope="col" />
                </tr>
              </thead>
              <tbody>
                {courses.map((course) => (
                  <tr key={course.id}>
                    <td>
                      {course.title}
                      <br />
                      <span className="kpi__hint">{course.category}</span>
                    </td>
                    <td>
                      {course.price_paise > 0 ? (
                        <Amount paise={course.price_paise} compact />
                      ) : (
                        <Badge tone="neutral">Free</Badge>
                      )}
                    </td>
                    <td>
                      <Badge tone={course.is_published ? 'success' : 'neutral'}>
                        {course.is_published ? 'Published' : 'Draft'}
                      </Badge>
                    </td>
                    <td>{course.topic_count}</td>
                    <td>{course.task_count}</td>
                    <td>
                      <Amount paise={course.total_reward} compact />
                    </td>
                    <td>{course.purchase_count}</td>
                    <td>
                      <div className="table__actions">
                        <Button
                          variant="secondary"
                          onClick={() =>
                            setSelectedCourse(selectedCourse?.id === course.id ? null : course)
                          }
                        >
                          {selectedCourse?.id === course.id ? 'Hide topics' : 'Topics'}
                        </Button>
                        <Button
                          variant="secondary"
                          onClick={() =>
                            setCourseForm({
                              mode: 'edit',
                              id: course.id,
                              values: courseToForm(course),
                            })
                          }
                        >
                          Edit
                        </Button>
                        <Button variant="secondary" onClick={() => removeCourse(course)}>
                          Delete
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {selectedCourse ? (
        <section className="card">
          <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h2 className="card__title">Topics in {selectedCourse.title}</h2>
              <p className="card__subtitle">Use the arrows to change the order learners see.</p>
            </div>
            <Button onClick={() => setTopicForm({ mode: 'create', values: EMPTY_TOPIC })}>
              Add topic
            </Button>
          </div>

          {!topics ? (
            <Loading label="Loading topics…" />
          ) : topics.length === 0 ? (
            <p>This course has no topics yet.</p>
          ) : (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th scope="col">#</th>
                    <th scope="col">Topic</th>
                    <th scope="col">Video</th>
                    <th scope="col">Tasks</th>
                    <th scope="col" />
                  </tr>
                </thead>
                <tbody>
                  {topics.map((topic, index) => (
                    <tr key={topic.id}>
                      <td>{topic.position}</td>
                      <td>{topic.title}</td>
                      <td>
                        {topic.video_url ? (
                          <Badge tone="info">Set</Badge>
                        ) : (
                          <Badge tone="neutral">None</Badge>
                        )}
                      </td>
                      <td>{topic.task_count}</td>
                      <td>
                        <div className="table__actions">
                          <Button
                            variant="secondary"
                            disabled={busy || index === 0}
                            onClick={() => shift(index, -1)}
                          >
                            ↑
                          </Button>
                          <Button
                            variant="secondary"
                            disabled={busy || index === topics.length - 1}
                            onClick={() => shift(index, 1)}
                          >
                            ↓
                          </Button>
                          <Button
                            variant="secondary"
                            onClick={() =>
                              setTopicForm({
                                mode: 'edit',
                                id: topic.id,
                                values: {
                                  title: topic.title,
                                  video_url: topic.video_url ?? '',
                                  content: topic.content,
                                },
                              })
                            }
                          >
                            Edit
                          </Button>
                          <Button variant="secondary" onClick={() => removeTopic(topic)}>
                            Delete
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      ) : null}

      {courseForm ? (
        <Modal
          title={courseForm.mode === 'create' ? 'New course' : 'Edit course'}
          onClose={() => setCourseForm(null)}
          wide
          footer={
            <>
              <Button variant="secondary" onClick={() => setCourseForm(null)}>
                Cancel
              </Button>
              <Button type="submit" form="course-form" disabled={busy}>
                {busy ? 'Saving…' : 'Save course'}
              </Button>
            </>
          }
        >
          <form id="course-form" className="stack" onSubmit={saveCourse}>
            <FormField
              id="course-title"
              label="Title"
              value={courseForm.values.title}
              onChange={(event) => setCourseValue('title', event.target.value)}
            />
            <FormField
              id="course-category"
              label="Category"
              value={courseForm.values.category}
              onChange={(event) => setCourseValue('category', event.target.value)}
            />

            <div className="form-grid">
              <FormField
                id="course-price"
                label="Price (₹)"
                type="number"
                min="0"
                step="1"
                required={false}
                value={courseForm.values.price_rupees}
                onChange={(event) => setCourseValue('price_rupees', event.target.value)}
                hint="What a learner pays from their wallet. Leave blank or 0 to keep it free."
              />
              <div className="field">
                <label className="field__label" htmlFor="course-level">
                  Level
                </label>
                <select
                  id="course-level"
                  className="field__input"
                  value={courseForm.values.level}
                  onChange={(event) => setCourseValue('level', event.target.value)}
                >
                  {LEVEL_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-grid">
              <FormField
                id="course-duration"
                label="Estimated duration (minutes)"
                type="number"
                min="0"
                step="15"
                required={false}
                value={courseForm.values.duration_minutes}
                onChange={(event) => setCourseValue('duration_minutes', event.target.value)}
                hint="Shown on the course card, e.g. 180 becomes 3h."
              />
              <FormField
                id="course-access"
                label="Access after purchase (days)"
                type="number"
                min="1"
                step="1"
                required={false}
                value={courseForm.values.access_days}
                onChange={(event) => setCourseValue('access_days', event.target.value)}
                hint="Leave blank for permanent access."
              />
            </div>

            <FormField
              id="course-cover"
              label="Cover image URL"
              required={false}
              value={courseForm.values.cover_image_url}
              onChange={(event) => setCourseValue('cover_image_url', event.target.value)}
              hint="A wide image used on the course card and its banner."
            />

            <div className="field">
              <label className="field__label" htmlFor="course-outcomes">
                Learning outcomes
              </label>
              <textarea
                id="course-outcomes"
                className="textarea"
                rows={3}
                placeholder="One outcome per line"
                value={courseForm.values.outcomes_text}
                onChange={(event) => setCourseValue('outcomes_text', event.target.value)}
              />
              <span className="field__hint">
                One per line. These become “What you will learn” on the course page.
              </span>
            </div>

            <div className="field">
              <label className="field__label" htmlFor="course-description">
                Description
              </label>
              <textarea
                id="course-description"
                className="textarea"
                value={courseForm.values.description}
                onChange={(event) => setCourseValue('description', event.target.value)}
              />
            </div>
            <Switch
              id="course-published"
              label="Published"
              checked={courseForm.values.is_published}
              onChange={(checked) => setCourseValue('is_published', checked)}
              hint="Draft courses are hidden from learners."
            />
          </form>
        </Modal>
      ) : null}

      {topicForm ? (
        <Modal
          title={topicForm.mode === 'create' ? 'Add topic' : 'Edit topic'}
          onClose={() => setTopicForm(null)}
          wide
          footer={
            <>
              <Button variant="secondary" onClick={() => setTopicForm(null)}>
                Cancel
              </Button>
              <Button type="submit" form="topic-form" disabled={busy}>
                {busy ? 'Saving…' : 'Save topic'}
              </Button>
            </>
          }
        >
          <form id="topic-form" className="stack" onSubmit={saveTopic}>
            <FormField
              id="topic-title"
              label="Title"
              value={topicForm.values.title}
              onChange={(event) =>
                setTopicForm({
                  ...topicForm,
                  values: { ...topicForm.values, title: event.target.value },
                })
              }
            />
            <FormField
              id="topic-video"
              label="Video URL"
              value={topicForm.values.video_url}
              required={false}
              onChange={(event) =>
                setTopicForm({
                  ...topicForm,
                  values: { ...topicForm.values, video_url: event.target.value },
                })
              }
              hint="Use the embed form of the link (e.g. https://www.youtube.com/embed/…)."
            />
            <div className="field">
              <label className="field__label" htmlFor="topic-content">
                Notes (Markdown)
              </label>
              <textarea
                id="topic-content"
                className="textarea"
                value={topicForm.values.content}
                onChange={(event) =>
                  setTopicForm({
                    ...topicForm,
                    values: { ...topicForm.values, content: event.target.value },
                  })
                }
              />
            </div>
          </form>
        </Modal>
      ) : null}
    </div>
  )
}

export default AdminCoursesPage
