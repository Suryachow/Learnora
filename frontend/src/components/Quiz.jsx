import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import * as attemptsApi from '../api/attempts'
import Amount from './Amount'
import Alert from './Alert'
import Badge from './Badge'
import Button from './Button'
import ProgressBar from './ProgressBar'
import { Loading } from './Spinner'
import { useAuth } from '../hooks/useAuth'

/**
 * The quiz screen. Questions are fetched only when the learner starts, and the
 * answers never leave the server - the browser only ever sends back the option
 * index it was given.
 */
export function QuizRunner({ task, onResult }) {
  const [quiz, setQuiz] = useState(null)
  const [answers, setAnswers] = useState({})
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [problem, setProblem] = useState('')

  useEffect(() => {
    let cancelled = false

    attemptsApi
      .fetchQuiz(task.id)
      .then((data) => {
        if (!cancelled) setQuiz(data)
      })
      .catch((err) => {
        if (!cancelled) setProblem(err.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [task.id])

  function choose(questionId, index) {
    setAnswers((current) => ({ ...current, [questionId]: index }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setProblem('')
    setSubmitting(true)

    try {
      const result = await attemptsApi.submitAttempt(task.id, answers)
      onResult(result)
    } catch (err) {
      setProblem(err.message)
      setSubmitting(false)
    }
  }

  if (loading) return <Loading label="Loading the questions…" />

  if (!quiz) {
    return (
      <div className="stack">
        <Alert>{problem || 'The questions could not be loaded.'}</Alert>
        <Link className="btn btn--secondary" to={`/topics/${task.topic_id}`}>
          Back to the material
        </Link>
      </div>
    )
  }

  const total = quiz.questions.length
  const answered = quiz.questions.filter((question) => answers[question.id] != null).length

  return (
    <form className="stack" onSubmit={handleSubmit}>
      <div className="quiz-header">
        <div>
          <h2 className="card__title">Questions</h2>
          <p className="card__subtitle">
            {answered} of {total} answered · {quiz.pass_percent}% needed to pass
          </p>
        </div>
        <div className="quiz-progress">
          <ProgressBar value={answered} max={total} label="Answered questions" />
        </div>
      </div>

      <Alert>{problem}</Alert>

      {quiz.questions.map((question, index) => (
        <div
          key={question.id}
          className="quiz-question"
          role="group"
          aria-labelledby={`question-prompt-${question.id}`}
        >
          <p className="quiz-question__prompt" id={`question-prompt-${question.id}`}>
            {index + 1}. {question.prompt}
          </p>
          <div className="quiz-options">
            {question.options.map((option, optionIndex) => (
              <label
                key={option}
                className="quiz-option"
                data-selected={answers[question.id] === optionIndex}
              >
                <input
                  type="radio"
                  name={`question-${question.id}`}
                  value={optionIndex}
                  checked={answers[question.id] === optionIndex}
                  onChange={() => choose(question.id, optionIndex)}
                />
                <span>{option}</span>
              </label>
            ))}
          </div>
        </div>
      ))}

      <div className="row">
        <Button type="submit" disabled={submitting || answered < total}>
          {submitting ? 'Grading…' : 'Submit answers'}
        </Button>
        <Link className="btn btn--secondary" to={`/topics/${task.topic_id}`}>
          Back to the material
        </Link>
      </div>

      <p className="card__subtitle">
        Answer every question to submit. Your score and the reward decision are made by the
        server.
      </p>
    </form>
  )
}

/** What the server decided about one submission. */
export function QuizResult({ task, result, onRetry }) {
  const { refresh } = useAuth()

  useEffect(() => {
    refresh()
  }, [refresh])

  return (
    <section className="card quiz-result">
      <p className="quiz-result__score">{result.percent}%</p>
      <p className="card__subtitle">
        {result.correct_count} of {result.question_count} correct · pass mark {task.pass_percent}%
      </p>

      <div className="row" style={{ justifyContent: 'center' }}>
        <Badge tone={result.passed ? 'success' : 'danger'}>
          {result.passed ? 'Passed' : 'Not passed'}
        </Badge>
      </div>

      <Alert tone={result.passed ? 'success' : 'warning'}>{result.message}</Alert>

      {result.reward_granted ? (
        <div className="card card--money">
          <h2 className="card__title">Reward paid</h2>
          <Amount paise={result.reward_paise} />
          <p className="card__subtitle">
            Added to your wallet and recorded in the ledger. <Link to="/wallet">Open wallet</Link>.
          </p>
        </div>
      ) : null}

      <div className="row" style={{ justifyContent: 'center' }}>
        <Button type="button" onClick={onRetry}>
          Try again
        </Button>
        <Link className="btn btn--secondary" to={`/topics/${task.topic_id}`}>
          Back to the material
        </Link>
      </div>
    </section>
  )
}

export default QuizRunner
