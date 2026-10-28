import { useCallback, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import * as catalogApi from '../api/catalog'
import * as progressApi from '../api/progress'
import Amount from '../components/Amount'
import Alert from '../components/Alert'
import Badge from '../components/Badge'
import Button from '../components/Button'
import EmptyState from '../components/EmptyState'
import LessonVideo, { youtubeId } from '../components/LessonVideo'
import Markdown from '../components/Markdown'
import { Loading } from '../components/Spinner'
import useFetch from '../hooks/useFetch'
import { useAuth } from '../hooks/useAuth'
import { formatRupees } from '../utils/money'

const RATINGS = [
  { value: 'confident', label: 'I understood it well and could explain it' },
  { value: 'mostly', label: 'Mostly — I have a few gaps to close' },
  { value: 'not_yet', label: 'Not yet — I want to watch it again' },
]

/**
 * "How was your understanding?" - the honest bit between the video and the
 * assessment. It is stored against the lesson and only opens once the video has
 * been watched to the end.
 */
function UnderstandingCheck({ topic, onSaved }) {
  const saved = topic.progress?.understanding ?? ''
  const [rating, setRating] = useState(saved)
  const [note, setNote] = useState(topic.progress?.understanding_note ?? '')
  const [saving, setSaving] = useState(false)
  const [problem, setProblem] = useState('')
  const [done, setDone] = useState(Boolean(topic.progress?.understood_at))

  async function handleSubmit(event) {
    event.preventDefault()
    setProblem('')
    setSaving(true)

    try {
      const progress = await progressApi.saveUnderstanding(topic.id, { rating, note })
      setDone(true)
      onSaved(progress)
    } catch (err) {
      setProblem(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="stack" onSubmit={handleSubmit}>
      <p className="card__subtitle">
        Be honest — your answer is for you and your instructor, and it is what unlocks the
        assessment below.
      </p>

      <div className="quiz-options">
        {RATINGS.map((option) => (
          <label
            key={option.value}
            className="quiz-option"
            data-selected={rating === option.value}
          >
            <input
              type="radio"
              name="understanding"
              value={option.value}
              checked={rating === option.value}
              onChange={() => setRating(option.value)}
            />
            <span>{option.label}</span>
          </label>
        ))}
      </div>

      <label className="field" htmlFor="understanding-note">
        <span className="field__label">Anything you want to note down? (optional)</span>
        <textarea
          id="understanding-note"
          className="field__input"
          rows={3}
          maxLength={1000}
          value={note}
          onChange={(event) => setNote(event.target.value)}
          placeholder="The part about loops still feels fuzzy…"
        />
      </label>

      <Alert>{problem}</Alert>

      {done ? (
        <Alert tone="success">
          Saved. You can change this at any time — the assessment stays unlocked.
        </Alert>
      ) : null}

      <div className="row">
        <Button type="submit" disabled={!rating || saving}>
          {saving ? 'Saving…' : done ? 'Update my answer' : 'Save and unlock the quiz'}
        </Button>
      </div>
    </form>
  )
}

/** Learning material, the video, the understanding check, and the assessments. */
export function TopicDetailPage() {
  const { topicId } = useParams()
  const { user } = useAuth()

  const loadTopic = useCallback(() => catalogApi.fetchTopic(topicId), [topicId])
  const { data: topic, loading, error, reload, setData } = useFetch(loadTopic)

  if (loading) return <Loading label="Loading this topic…" />

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

  if (!topic) return null

  const locked = topic.is_locked
  const subscribed = Boolean(user?.has_active_subscription)
  // A paid course answers to its purchase; a free one to the subscription.
  const mayAssess = topic.has_course_access && (!topic.requires_subscription || subscribed)
  // Only YouTube lessons can be tracked, so only they hold the quiz back.
  const trackable = Boolean(youtubeId(topic.video_url))
  const videoDone = Boolean(topic.progress?.video_completed_at)
  const understood = Boolean(topic.progress?.understood_at)
  const ready = !trackable || (videoDone && understood)
  const canAssess = mayAssess && ready

  function applyProgress(progress) {
    setData((current) => ({ ...current, progress }))
  }

  return (
    <div className="stack">
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link to="/courses">Courses</Link>
        <span aria-hidden="true">/</span>
        <Link to={`/courses/${topic.course_id}`}>{topic.course_title}</Link>
        <span aria-hidden="true">/</span>
        <span>{topic.title}</span>
      </nav>

      <header className="page-header">
        <h1>{topic.title}</h1>
        <p>
          Topic {topic.position + 1} of {topic.course_title}
        </p>
      </header>

      {topic.video_url ? (
        trackable ? (
          <LessonVideo
            topicId={topic.id}
            title={topic.title}
            url={topic.video_url}
            completed={videoDone}
            signedIn={Boolean(user)}
            onCompleted={applyProgress}
          />
        ) : (
          <div className="video-frame">
            <iframe
              src={topic.video_url}
              title={`Video lesson: ${topic.title}`}
              loading="lazy"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>
        )
      ) : null}

      {trackable ? (
        <section className="card">
          <div className="section__header">
            <h2 className="card__title">How was your understanding?</h2>
            {understood ? <Badge tone="success">Recorded</Badge> : null}
          </div>

          {!user ? (
            <>
              <p className="card__subtitle">
                Sign in to record how the lesson went. That is what unlocks the assessment, and it
                saves your progress across devices.
              </p>
              <div className="row">
                <Link className="btn btn--primary" to="/login">
                  Sign in
                </Link>
              </div>
            </>
          ) : !videoDone ? (
            <p className="card__subtitle">
              Watch the video all the way to the end first — this opens when it finishes.
            </p>
          ) : (
            <UnderstandingCheck
              key={topic.progress?.understood_at ?? 'new'}
              topic={topic}
              onSaved={applyProgress}
            />
          )}
        </section>
      ) : null}

      {locked ? (
        <section className="paywall">
          <span className="paywall__label">Paid course</span>
          <h2 className="paywall__title">{topic.course_title}</h2>
          <p className="paywall__note">
            This lesson and its assessments are part of a paid course. One payment opens every
            topic in it — a subscription is not needed.
          </p>

          <div className="paywall__action">
            <Amount paise={topic.course_price_paise} label="Course price" compact />
            {user ? (
              <Link className="btn btn--primary" to={`/checkout/${topic.course_id}`}>
                Select this course — {formatRupees(topic.course_price_paise)}
              </Link>
            ) : (
              <Link className="btn btn--primary" to="/login">
                Sign in to unlock
              </Link>
            )}
            <Link className="btn btn--secondary" to={`/courses/${topic.course_id}`}>
              See what is inside
            </Link>
          </div>
        </section>
      ) : (
        <section className="card">
          <h2 className="card__title">Learning material</h2>
          <Markdown>{topic.content}</Markdown>
        </section>
      )}

      <section className="section">
        <div className="section__header">
          <h2 className="section__title">Assessments in this topic</h2>
          {topic.total_reward > 0 ? (
            <Amount paise={topic.total_reward} label="Total reward" compact />
          ) : null}
        </div>

        {!mayAssess && !locked && topic.tasks.length > 0 ? (
          <Alert tone="info">
            A subscription unlocks these tasks and the rewards they pay. You can keep reading the
            material for free in the meantime.
          </Alert>
        ) : null}

        {mayAssess && !ready ? (
          <Alert tone="info">
            {user
              ? 'Watch the video to the end and answer the understanding check to unlock the assessments in this topic.'
              : 'Sign in, watch the video to the end and answer the understanding check to unlock the assessments in this topic.'}
          </Alert>
        ) : null}

        {topic.tasks.length === 0 ? (
          <EmptyState title="No assessment in this topic yet">
            Read the material now — the assessment for this topic will appear here once it is
            published.
          </EmptyState>
        ) : (
          <ul className="task-list">
            {topic.tasks.map((task) => (
              <li key={task.id} className="task-card">
                <div className="task-card__head">
                  <h3 className="task-card__title">{task.title}</h3>
                  <Amount paise={task.reward} label="Reward" compact />
                </div>
                <div className="task-card__meta">
                  <span className="pill pill--soft">
                    {task.type === 'quiz' ? 'Quiz' : 'Coding task'}
                  </span>
                  <span>
                    {task.question_count}{' '}
                    {task.question_count === 1 ? 'question' : 'questions'}
                  </span>
                  <span>Pass mark {task.pass_percent}%</span>
                </div>

                {canAssess ? (
                  <Link className="btn btn--primary" to={`/tasks/${task.id}/quiz`}>
                    Start the quiz
                  </Link>
                ) : (
                  <>
                    <Button variant="secondary" disabled>
                      Locked
                    </Button>
                    <span className="task-card__lock">
                      {mayAssess
                        ? 'Finish the lesson to unlock this assessment.'
                        : locked
                          ? 'Buy the course to open this assessment.'
                          : 'A subscription opens this assessment.'}
                    </span>
                  </>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      <div className="row">
        <Link className="btn btn--secondary" to={`/courses/${topic.course_id}`}>
          Back to {topic.course_title}
        </Link>
      </div>
    </div>
  )
}

export default TopicDetailPage
