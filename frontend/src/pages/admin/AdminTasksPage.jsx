import { useCallback, useEffect, useState } from 'react'

import {
  createTask,
  deleteTask,
  fetchCourses,
  fetchTask,
  fetchTasks,
  fetchTopics,
  updateTask,
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
import { formatRupees } from '../../utils/money'

const EMPTY_QUESTION = () => ({
  prompt: '',
  options: ['', ''],
  correct_index: 0,
  points: 1,
})

const EMPTY_TASK = {
  courseId: '',
  topic_id: '',
  title: '',
  pass_percent: 70,
  reward_rupees: 0,
  is_active: true,
  questions: [EMPTY_QUESTION()],
}

/** The quiz builder: one task, its knobs, and its questions. */
function TaskBuilder({ form, courses, onChange, onClose, onSubmit, busy, error }) {
  const [topics, setTopics] = useState(null)

  useEffect(() => {
    if (!form.courseId) {
      setTopics(null)
      return undefined
    }
    let cancelled = false
    fetchTopics(form.courseId)
      .then((rows) => {
        if (!cancelled) setTopics(rows)
      })
      .catch(() => {
        if (!cancelled) setTopics([])
      })
    return () => {
      cancelled = true
    }
  }, [form.courseId])

  function setValue(patch) {
    onChange({ ...form, ...patch })
  }

  function setQuestion(index, patch) {
    const questions = form.questions.map((question, position) =>
      position === index ? { ...question, ...patch } : question,
    )
    setValue({ questions })
  }

  function setOption(qIndex, oIndex, text) {
    const question = form.questions[qIndex]
    const options = question.options.map((option, position) =>
      position === oIndex ? text : option,
    )
    setQuestion(qIndex, { options })
  }

  function addOption(qIndex) {
    const question = form.questions[qIndex]
    if (question.options.length >= 8) return
    setQuestion(qIndex, { options: [...question.options, ''] })
  }

  function removeOption(qIndex, oIndex) {
    const question = form.questions[qIndex]
    if (question.options.length <= 2) return
    const options = question.options.filter((_, position) => position !== oIndex)
    const correct_index =
      question.correct_index >= options.length ? options.length - 1 : question.correct_index
    setQuestion(qIndex, { options, correct_index })
  }

  return (
    <Modal
      title={form.mode === 'create' ? 'New quiz task' : 'Edit quiz task'}
      onClose={onClose}
      wide
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" form="task-form" disabled={busy}>
            {busy ? 'Saving…' : 'Save task'}
          </Button>
        </>
      }
    >
      <form id="task-form" className="stack" onSubmit={onSubmit}>
        <Alert>{error}</Alert>

        <div className="form-grid">
          <div className="field">
            <label className="field__label" htmlFor="task-course">
              Course
            </label>
            <select
              id="task-course"
              className="field__input"
              value={form.courseId}
              onChange={(event) => setValue({ courseId: event.target.value, topic_id: '' })}
              required
            >
              <option value="">Choose a course…</option>
              {courses.map((course) => (
                <option key={course.id} value={course.id}>
                  {course.title}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label className="field__label" htmlFor="task-topic">
              Topic
            </label>
            <select
              id="task-topic"
              className="field__input"
              value={form.topic_id}
              onChange={(event) => setValue({ topic_id: event.target.value })}
              required
              disabled={!form.courseId}
            >
              <option value="">Choose a topic…</option>
              {(topics ?? []).map((topic) => (
                <option key={topic.id} value={topic.id}>
                  {topic.title}
                </option>
              ))}
            </select>
          </div>

          <FormField
            id="task-title"
            label="Title"
            value={form.title}
            onChange={(event) => setValue({ title: event.target.value })}
          />

          <FormField
            id="task-pass"
            label="Pass mark (%)"
            type="number"
            value={form.pass_percent}
            onChange={(event) => setValue({ pass_percent: event.target.value })}
          />

          <FormField
            id="task-reward"
            label="Reward (₹)"
            type="number"
            value={form.reward_rupees}
            onChange={(event) => setValue({ reward_rupees: event.target.value })}
            hint={`Stored as ${Math.round((Number(form.reward_rupees) || 0) * 100)} paise. A per-task cap in settings still applies.`}
          />
        </div>

        <Switch
          id="task-active"
          label="Open to learners"
          checked={form.is_active}
          onChange={(checked) => setValue({ is_active: checked })}
          hint="Inactive tasks stay in the catalogue but cannot be attempted."
        />

        <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 className="card__title">Questions</h3>
          <Button
            variant="secondary"
            onClick={() => setValue({ questions: [...form.questions, EMPTY_QUESTION()] })}
          >
            Add question
          </Button>
        </div>

        {form.questions.map((question, qIndex) => (
          <section className="quiz-question" key={`question-${qIndex}`}>
            <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
              <strong>Question {qIndex + 1}</strong>
              <Button
                variant="secondary"
                disabled={form.questions.length === 1}
                onClick={() =>
                  setValue({
                    questions: form.questions.filter((_, position) => position !== qIndex),
                  })
                }
              >
                Remove
              </Button>
            </div>

            <div className="field">
              <label className="field__label" htmlFor={`prompt-${qIndex}`}>
                Prompt
              </label>
              <input
                id={`prompt-${qIndex}`}
                className="field__input"
                value={question.prompt}
                onChange={(event) => setQuestion(qIndex, { prompt: event.target.value })}
                required
              />
            </div>

            <div className="stack">
              {question.options.map((option, oIndex) => (
                <div className="field-row" key={`option-${oIndex}`}>
                  <label className="checkbox-line" style={{ flex: '0 0 auto' }}>
                    <input
                      type="radio"
                      name={`correct-${qIndex}`}
                      checked={question.correct_index === oIndex}
                      onChange={() => setQuestion(qIndex, { correct_index: oIndex })}
                    />
                    <span>Correct</span>
                  </label>
                  <input
                    className="field__input"
                    style={{ flex: 1 }}
                    aria-label={`Option ${oIndex + 1}`}
                    value={option}
                    onChange={(event) => setOption(qIndex, oIndex, event.target.value)}
                    required
                  />
                  <Button
                    variant="secondary"
                    disabled={question.options.length <= 2}
                    onClick={() => removeOption(qIndex, oIndex)}
                  >
                    ✕
                  </Button>
                </div>
              ))}
            </div>

            <div className="field-row">
              <Button
                variant="secondary"
                disabled={question.options.length >= 8}
                onClick={() => addOption(qIndex)}
              >
                Add option
              </Button>
              <label className="checkbox-line">
                <span className="kpi__hint">Points</span>
                <input
                  className="field__input"
                  type="number"
                  min="1"
                  max="100"
                  style={{ width: 90 }}
                  aria-label={`Points for question ${qIndex + 1}`}
                  value={question.points}
                  onChange={(event) => setQuestion(qIndex, { points: event.target.value })}
                />
              </label>
            </div>
          </section>
        ))}
      </form>
    </Modal>
  )
}

/** Tasks across the catalogue, with the quiz builder for each. */
export function AdminTasksPage() {
  const [search, setSearch] = useState('')
  const [query, setQuery] = useState('')
  const [courseFilter, setCourseFilter] = useState('')
  const [form, setForm] = useState(null)
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const [formError, setFormError] = useState('')
  const [notice, setNotice] = useState('')

  const loadCourses = useCallback(() => fetchCourses(), [])
  const { data: courses } = useFetch(loadCourses)

  const loadTasks = useCallback(
    () =>
      fetchTasks({
        search: query || undefined,
        courseId: courseFilter || undefined,
      }),
    [query, courseFilter],
  )
  const { data: tasks, loading, error, reload } = useFetch(loadTasks)

  async function openBuilder(taskId) {
    setProblem('')
    setFormError('')

    if (!taskId) {
      setForm({ mode: 'create', ...EMPTY_TASK })
      return
    }

    try {
      const detail = await fetchTask(taskId)
      setForm({
        mode: 'edit',
        id: detail.id,
        courseId: String(detail.course_id),
        topic_id: String(detail.topic_id),
        title: detail.title,
        pass_percent: detail.pass_percent,
        reward_rupees: detail.reward / 100,
        is_active: detail.is_active,
        questions: detail.questions.length
          ? detail.questions.map((question) => ({
              id: question.id,
              prompt: question.prompt,
              options: question.options,
              correct_index: question.correct_index,
              points: question.points,
            }))
          : [EMPTY_QUESTION()],
      })
    } catch (err) {
      setProblem(err.message)
    }
  }

  async function saveTask(event) {
    event.preventDefault()
    setFormError('')

    const questions = form.questions.map((question) => ({
      id: question.id,
      prompt: question.prompt.trim(),
      options: question.options.map((option) => option.trim()),
      correct_index: Number(question.correct_index),
      points: Number(question.points) || 1,
    }))

    if (!form.topic_id) {
      setFormError('Choose the course and topic this task belongs to.')
      return
    }
    if (questions.some((question) => !question.prompt || question.options.some((o) => !o))) {
      setFormError('Every question needs a prompt and all of its options filled in.')
      return
    }

    const payload = {
      topic_id: Number(form.topic_id),
      title: form.title.trim(),
      pass_percent: Number(form.pass_percent),
      reward: Math.round((Number(form.reward_rupees) || 0) * 100),
      is_active: form.is_active,
      questions,
    }

    setBusy(true)
    try {
      if (form.mode === 'create') {
        await createTask(payload)
        setNotice('Task created.')
      } else {
        await updateTask(form.id, payload)
        setNotice('Task updated.')
      }
      setForm(null)
      reload()
    } catch (err) {
      setFormError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function removeTask(task) {
    if (!window.confirm(`Delete “${task.title}” and the attempts recorded against it?`)) return
    setProblem('')
    setNotice('')
    try {
      await deleteTask(task.id)
      setNotice('Task deleted.')
      reload()
    } catch (err) {
      setProblem(err.message)
    }
  }

  return (
    <div className="stack">
      <header className="page-header">
        <h1>Tasks and quizzes</h1>
        <p>Write the questions, set the pass mark and decide what passing is worth.</p>
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
            aria-label="Search tasks"
            placeholder="Search tasks"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <select
            className="field__input"
            aria-label="Filter by course"
            value={courseFilter}
            onChange={(event) => setCourseFilter(event.target.value)}
          >
            <option value="">All courses</option>
            {(courses ?? []).map((course) => (
              <option key={course.id} value={course.id}>
                {course.title}
              </option>
            ))}
          </select>
          <Button type="submit" variant="secondary">
            Apply
          </Button>
        </form>
        <div className="toolbar__actions">
          <Button onClick={() => openBuilder(null)} disabled={!courses?.length}>
            New task
          </Button>
        </div>
      </div>

      {loading ? <Loading label="Loading tasks…" /> : null}

      {error ? (
        <div className="stack">
          <Alert>{error.message}</Alert>
          <button type="button" className="btn btn--secondary" onClick={reload}>
            Try again
          </button>
        </div>
      ) : null}

      {tasks ? (
        <section className="card">
          <h2 className="card__title">
            {tasks.length} task{tasks.length === 1 ? '' : 's'}
          </h2>

          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">Task</th>
                  <th scope="col">Where</th>
                  <th scope="col">Pass</th>
                  <th scope="col">Reward</th>
                  <th scope="col">Questions</th>
                  <th scope="col">Claimed</th>
                  <th scope="col">Status</th>
                  <th scope="col" />
                </tr>
              </thead>
              <tbody>
                {tasks.map((task) => (
                  <tr key={task.id}>
                    <td>{task.title}</td>
                    <td>
                      {task.course_title}
                      <br />
                      <span className="kpi__hint">{task.topic_title}</span>
                    </td>
                    <td>{task.pass_percent}%</td>
                    <td>
                      <Amount paise={task.reward} compact />
                      <br />
                      <span className="kpi__hint">worth {formatRupees(task.reward)}</span>
                    </td>
                    <td>{task.question_count}</td>
                    <td>{task.reward_claim_count}</td>
                    <td>
                      <Badge tone={task.is_active ? 'success' : 'neutral'}>
                        {task.is_active ? 'Open' : 'Closed'}
                      </Badge>
                    </td>
                    <td>
                      <div className="table__actions">
                        <Button variant="secondary" onClick={() => openBuilder(task.id)}>
                          Edit
                        </Button>
                        <Button variant="secondary" onClick={() => removeTask(task)}>
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

      {form ? (
        <TaskBuilder
          form={form}
          courses={courses ?? []}
          onChange={setForm}
          onClose={() => setForm(null)}
          onSubmit={saveTask}
          busy={busy}
          error={formError}
        />
      ) : null}
    </div>
  )
}

export default AdminTasksPage
