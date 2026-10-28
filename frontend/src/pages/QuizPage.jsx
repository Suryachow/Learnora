import { useCallback, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import * as catalogApi from '../api/catalog'
import Amount from '../components/Amount'
import Alert from '../components/Alert'
import Button from '../components/Button'
import { QuizResult, QuizRunner } from '../components/Quiz'
import { Loading } from '../components/Spinner'
import useFetch from '../hooks/useFetch'

/**
 * The assessment on its own screen, reached only after the lesson video has
 * been watched to the end and the understanding check has been answered.
 *
 * The questions are fetched here rather than on the topic page, and the server
 * refuses them outright until the lesson is done - so the link is a convenience,
 * not the gate.
 */
export function QuizPage() {
  const { taskId } = useParams()
  const [round, setRound] = useState(0)
  const [result, setResult] = useState(null)

  const loadTask = useCallback(() => catalogApi.fetchTask(taskId), [taskId])
  const { data: task, loading, error, reload } = useFetch(loadTask)

  if (loading) return <Loading label="Opening the quiz…" />

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

  return (
    <div className="stack">
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link to="/courses">Courses</Link>
        <span aria-hidden="true">/</span>
        <Link to={`/topics/${task.topic_id}`}>Lesson</Link>
        <span aria-hidden="true">/</span>
        <span>{task.title}</span>
      </nav>

      <header className="page-header">
        <span className="pill pill--soft">Quiz</span>
        <h1>{task.title}</h1>
        <p>
          {task.question_count} {task.question_count === 1 ? 'question' : 'questions'} · pass mark{' '}
          {task.pass_percent}%
        </p>
      </header>

      {task.type !== 'quiz' ? (
        <div className="stack">
          <Alert tone="info">
            This assessment is not a quiz yet. It stays available, and your progress will carry
            over.
          </Alert>
          <div className="row">
            <Link className="btn btn--secondary" to={`/topics/${task.topic_id}`}>
              Back to the lesson
            </Link>
          </div>
        </div>
      ) : (
        <>
          <div className="quiz-banner">
            <span>Reward on passing</span>
            <Amount paise={task.reward} compact />
          </div>

          {result ? (
            <QuizResult
              task={task}
              result={result}
              onRetry={() => {
                setRound((value) => value + 1)
                setResult(null)
              }}
            />
          ) : (
            <QuizRunner key={round} task={task} onResult={setResult} />
          )}
        </>
      )}
    </div>
  )
}

export default QuizPage
