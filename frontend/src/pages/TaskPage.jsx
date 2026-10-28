import { useCallback } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import * as attemptsApi from '../api/attempts'
import * as catalogApi from '../api/catalog'
import Amount from '../components/Amount'
import Alert from '../components/Alert'
import Badge from '../components/Badge'
import Button from '../components/Button'
import { Loading } from '../components/Spinner'
import useFetch from '../hooks/useFetch'
import { useAuth } from '../hooks/useAuth'
import { formatDateTime } from '../utils/datetime'

/**
 * The briefing for one assessment: what it pays, what it takes to pass, and what
 * the server does with a submission. The questions themselves live on the quiz
 * screen, which the server refuses until the lesson video has been watched.
 */
export function TaskPage() {
  const { taskId } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()

  const loadTask = useCallback(() => catalogApi.fetchTask(taskId), [taskId])
  const { data: task, loading, error, reload } = useFetch(loadTask)

  const loadAttempts = useCallback(
    () => (user ? attemptsApi.fetchMyAttempts({ limit: 5 }) : Promise.resolve(null)),
    [user],
  )
  const { data: attempts } = useFetch(loadAttempts)

  if (loading) return <Loading label="Loading this task…" />

  if (error) {
    return (
      <div className="stack">
        <Alert>{error.message}</Alert>
        <div className="row">
          <Button variant="secondary" onClick={reload}>
            Try again
          </Button>
          <Link className="btn btn--secondary" to="/courses">
            Back to all courses
          </Link>
        </div>
      </div>
    )
  }

  if (!task) return null

  const subscribed = Boolean(user?.has_active_subscription)
  const isQuiz = task.type === 'quiz'

  return (
    <div className="stack">
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link to="/courses">Courses</Link>
        <span aria-hidden="true">/</span>
        <Link to={`/topics/${task.topic_id}`}>Topic</Link>
        <span aria-hidden="true">/</span>
        <span>{task.title}</span>
      </nav>

      <header className="page-header">
        <span className="pill pill--soft">{isQuiz ? 'Quiz' : 'Coding task'}</span>
        <h1>{task.title}</h1>
        <p>Read the rules below, then start when you are ready.</p>
      </header>

      <div className="grid">
        <section className="card card--money">
          <h2 className="card__title">Reward</h2>
          <Amount paise={task.reward} />
          <p className="card__subtitle">
            Paid once, the first time you pass. It is added to your wallet by the server, never by
            the browser.
          </p>
        </section>

        <section className="card">
          <h2 className="card__title">What it takes to pass</h2>
          <dl className="definition-list">
            <dt>Pass mark</dt>
            <dd>{task.pass_percent}%</dd>
            <dt>Questions</dt>
            <dd>{task.question_count}</dd>
            <dt>Type</dt>
            <dd>{isQuiz ? 'Multiple choice quiz' : 'Coding challenge'}</dd>
          </dl>
        </section>
      </div>

      {!subscribed ? (
        <Alert tone="info">
          You need an active subscription before you can attempt this task.{' '}
          <Link to="/subscription">See the subscription</Link>.
        </Alert>
      ) : null}

      <section className="card">
        <h2 className="card__title">Before you start</h2>
        <ul className="prose__list">
          <li>
            Watch the lesson video all the way to the end — skipping ahead is disabled, and the
            video counts as watched only when it finishes.
          </li>
          <li>Tell us how well you understood it. That answer is what opens this assessment.</li>
          <li>
            Your answers are graded on the server, so the result cannot be edited in the browser.
          </li>
          <li>One reward per task per account, enforced by a database constraint.</li>
          <li>
            Read the <Link to="/rewards-policy">Rewards Policy</Link> before you rely on a payout
            date.
          </li>
        </ul>
      </section>

      {!isQuiz ? (
        <Alert tone="info">
          Coding challenges run in a sandbox that is not switched on yet. This task stays
          available, and your progress will carry over.
        </Alert>
      ) : null}

      <div className="row">
        <Button disabled={!subscribed || !isQuiz} onClick={() => navigate(`/tasks/${task.id}/quiz`)}>
          Start the quiz
        </Button>
        <Link className="btn btn--secondary" to={`/topics/${task.topic_id}`}>
          Back to the lesson
        </Link>
      </div>

      {attempts?.items?.length ? (
        <section className="card">
          <h2 className="card__title">Your recent attempts</h2>
          <table className="table">
            <thead>
              <tr>
                <th scope="col">When</th>
                <th scope="col">Task</th>
                <th scope="col">Score</th>
                <th scope="col">Result</th>
              </tr>
            </thead>
            <tbody>
              {attempts.items.map((attempt) => (
                <tr key={attempt.id}>
                  <td>{formatDateTime(attempt.created_at)}</td>
                  <td>
                    <Link to={`/tasks/${attempt.task_id}`}>
                      {attempt.task_title ?? `Task #${attempt.task_id}`}
                    </Link>
                  </td>
                  <td>{attempt.percent}%</td>
                  <td>
                    <Badge tone={attempt.passed ? 'success' : 'neutral'}>
                      {attempt.passed ? 'Passed' : 'Not passed'}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}
    </div>
  )
}

export default TaskPage
