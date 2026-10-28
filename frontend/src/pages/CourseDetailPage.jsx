import { useCallback } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'

import * as catalogApi from '../api/catalog'
import Alert from '../components/Alert'
import Badge from '../components/Badge'
import Button from '../components/Button'
import EmptyState from '../components/EmptyState'
import { Loading } from '../components/Spinner'
import useFetch from '../hooks/useFetch'
import { useAuth } from '../hooks/useAuth'
import { useReveal } from '../hooks/useReveal'
import { LEVEL_LABELS, formatDuration } from '../utils/course'
import { formatDate } from '../utils/datetime'
import { formatPaise, formatRupees } from '../utils/money'

const FREE_LOOP = [
  {
    title: 'Read and watch free',
    body: 'Notes and video are open to everyone, subscribed or not.',
  },
  {
    title: 'Assess when subscribed',
    body: 'A subscription unlocks the graded task at the end of each topic.',
  },
  {
    title: 'Rewards land in the ledger',
    body: 'Passing records a reward you can audit line by line in your wallet.',
  },
]

const PAID_LOOP = [
  {
    title: 'Pay once for the whole course',
    body: 'One payment opens every topic and every graded task — no subscription needed.',
  },
  {
    title: 'Read, watch and assess',
    body: 'The lessons and their assessments open as soon as the payment is confirmed.',
  },
  {
    title: 'Rewards land in the ledger',
    body: 'Passing still pays, and the payment itself is a line in your transaction history.',
  },
]

/** One course: what it covers, and every topic inside it. */
export function CourseDetailPage() {
  const { courseId } = useParams()
  const { user } = useAuth()
  const revealRef = useReveal()
  const [searchParams] = useSearchParams()
  // The checkout page sends people back here once the payment is confirmed.
  const justPaid = searchParams.get('paid') === '1'

  const loadCourse = useCallback(() => catalogApi.fetchCourse(courseId), [courseId])
  const { data: course, loading, error, reload } = useFetch(loadCourse)

  if (loading) return <Loading label="Loading this course…" />

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

  if (!course) return null

  const paid = course.price_paise > 0
  const owned = !paid || course.has_access
  const duration = formatDuration(course.duration_minutes)
  const loop = paid ? PAID_LOOP : FREE_LOOP

  return (
    <div className="stack" ref={revealRef}>
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link to="/courses">Courses</Link>
        <span aria-hidden="true">/</span>
        <span>{course.title}</span>
      </nav>

      <header className="course-banner" data-reveal>
        <div className="course-banner__lead">
          {course.cover_image_url ? (
            <img className="course-banner__cover" src={course.cover_image_url} alt="" />
          ) : null}

          <div className="course-head">
            <div className="course-card__tags">
              <span className="pill">{course.category}</span>
              <span className="pill pill--soft">
                {LEVEL_LABELS[course.level] ?? course.level}
              </span>
              {duration ? <span className="pill pill--soft">{duration}</span> : null}
            </div>
            <h1>{course.title}</h1>
            <p>{course.description}</p>
          </div>
        </div>

        <div className="course-banner__stats">
          <div className="course-banner__stat">
            <span>Topics</span>
            <strong>{course.topic_count}</strong>
          </div>
          <div className="course-banner__stat">
            <span>Assessments</span>
            <strong>{course.task_count}</strong>
          </div>
          <div className="course-banner__stat">
            <span>Rewards available</span>
            <strong className="is-money">{formatPaise(course.total_reward)}</strong>
          </div>
        </div>
      </header>

      {paid ? (
        <section className="course-buy" data-reveal>
          <div className="course-buy__copy">
            <span className="course-buy__label">Course price</span>
            <strong className="course-buy__price">{formatRupees(course.price_paise)}</strong>
            <span className="course-buy__note">
              {course.access_days
                ? `${course.access_days} days of access, counted from the day you buy.`
                : 'One payment, permanent access — no subscription needed.'}
            </span>
          </div>

          <div className="course-buy__action">
            {owned ? (
              <>
                <Badge tone="success">Unlocked</Badge>
                <span className="course-buy__note">
                  {course.access_expires_at
                    ? `Access until ${formatDate(course.access_expires_at)}.`
                    : 'Your access does not expire.'}
                </span>
              </>
            ) : user ? (
              <Link className="btn btn--primary" to={`/checkout/${course.id}`}>
                Select this course — {formatRupees(course.price_paise)}
              </Link>
            ) : (
              <Link className="btn btn--primary" to="/login">
                Sign in to unlock
              </Link>
            )}
          </div>
        </section>
      ) : null}

      {justPaid ? (
        <Alert tone="success">
          Payment confirmed — every topic and assessment in this course is open now.
        </Alert>
      ) : null}

      {course.outcomes.length > 0 ? (
        <section className="section" data-reveal>
          <div className="section__header">
            <h2 className="section__title">What you will learn</h2>
          </div>
          <ul className="course-outcomes">
            {course.outcomes.map((outcome) => (
              <li key={outcome}>{outcome}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="section">
        <div className="section__header">
          <h2 className="section__title">Topics in this course</h2>
          <p className="muted">
            {owned
              ? 'Work through them in order, or jump to the one you need.'
              : 'The list is public — buy the course to open the notes and the assessments.'}
          </p>
        </div>

        {course.topics.length === 0 ? (
          <EmptyState title="No topics published yet">
            Materials appear here as soon as an administrator adds them to this course.
          </EmptyState>
        ) : (
          <ol className="topic-grid" data-stagger>
            {course.topics.map((topic, index) => (
              <li key={topic.id}>
                <Link className="topic-row" to={`/topics/${topic.id}`}>
                  <span className="topic-row__index" aria-hidden="true">
                    {index + 1}
                  </span>
                  <span className="topic-row__body">
                    <span className="topic-row__title">{topic.title}</span>
                    <span className="topic-row__meta">
                      {topic.has_video ? <span className="pill pill--soft">Video</span> : null}
                      <span>
                        {topic.task_count} {topic.task_count === 1 ? 'task' : 'tasks'}
                      </span>
                    </span>
                  </span>
                  <span className="topic-row__open">
                    {owned ? 'Open topic' : 'Buy to open'}
                  </span>
                </Link>
              </li>
            ))}
          </ol>
        )}
      </section>

      <section className="section">
        <div className="section__header">
          <h2 className="section__title">How this course pays</h2>
          <Link to="/rewards-policy">Read the full policy</Link>
        </div>

        <div className="info-strip">
          {loop.map((item) => (
            <div key={item.title}>
              <strong>{item.title}</strong>
              <span>{item.body}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

export default CourseDetailPage
