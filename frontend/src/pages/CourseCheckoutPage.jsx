import { useCallback, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import * as catalogApi from '../api/catalog'
import Alert from '../components/Alert'
import Amount from '../components/Amount'
import Button from '../components/Button'
import { Loading } from '../components/Spinner'
import useFetch from '../hooks/useFetch'
import { LEVEL_LABELS, formatDuration } from '../utils/course'
import { formatPaise, formatRupees } from '../utils/money'

/**
 * Selecting one course, and paying for it.
 *
 * The only step the browser is allowed to take is opening the order. The course
 * opens when the payment provider's signed callback says the money arrived, so
 * this page waits for the server rather than trusting the click.
 */
export function CourseCheckoutPage() {
  const { courseId } = useParams()

  const loadCourse = useCallback(() => catalogApi.fetchCourse(courseId), [courseId])
  const { data: course, loading, error, reload } = useFetch(loadCourse)

  const [order, setOrder] = useState(null)
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const [justPaid, setJustPaid] = useState(false)

  async function startPayment() {
    setProblem('')
    setBusy(true)
    try {
      setOrder(await catalogApi.createCourseCheckout(courseId))
    } catch (err) {
      setProblem(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function confirmPayment() {
    setProblem('')
    setBusy(true)
    try {
      await catalogApi.simulateCoursePayment(courseId, order.order_id)
      setOrder(null)
      setJustPaid(true)
      reload()
    } catch (err) {
      setProblem(err.message)
    } finally {
      setBusy(false)
    }
  }

  if (loading) return <Loading label="Loading the checkout…" />

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

  const free = course.price_paise <= 0
  const owned = course.has_access || justPaid
  const duration = formatDuration(course.duration_minutes)
  const testGateway = Boolean(order?.provider === 'mock' && order?.mock_payment_url)

  return (
    <div className="stack">
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link to="/courses">Courses</Link>
        <span aria-hidden="true">/</span>
        <Link to={`/courses/${course.id}`}>{course.title}</Link>
        <span aria-hidden="true">/</span>
        <span>Checkout</span>
      </nav>

      <header className="page-header">
        <h1>Checkout</h1>
        <p>
          One payment for the whole course. Nothing unlocks until the payment provider confirms
          the payment.
        </p>
      </header>

      <div className="sub-layout">
        <div className="sub-main">
          {owned ? (
            <section className="card card--highlight">
              <p className="pill">{justPaid ? 'Payment confirmed' : 'Already yours'}</p>
              <h2 className="card__title">
                {justPaid ? `${course.title} is unlocked` : `You already own ${course.title}`}
              </h2>
              <p className="card__subtitle">
                {justPaid
                  ? 'The server confirmed the payment. Every lesson, video and assessment in this course is open now.'
                  : 'There is nothing to pay for this course again — it is already open to you.'}
              </p>
              <div className="row">
                <Link className="btn btn--primary" to={`/courses/${course.id}?paid=1`}>
                  Open the course
                </Link>
                {course.topics.length > 0 ? (
                  <Link className="btn btn--secondary" to={`/topics/${course.topics[0].id}`}>
                    Start the first lesson
                  </Link>
                ) : null}
              </div>
            </section>
          ) : free ? (
            <section className="card">
              <p className="pill">Free course</p>
              <h2 className="card__title">Nothing to pay for {course.title}</h2>
              <p className="card__subtitle">
                Its lessons are open to everyone. A subscription is what unlocks the assessments.
              </p>
              <div className="row">
                <Link className="btn btn--primary" to={`/courses/${course.id}`}>
                  Open the course
                </Link>
                <Link className="btn btn--secondary" to="/subscription">
                  See the subscription
                </Link>
              </div>
            </section>
          ) : (
            <section className="card card--highlight">
              <p className="pill">Selected course</p>
              <h2 className="card__title">{course.title}</h2>
              <p className="card__subtitle">{course.description}</p>

              <div className="sub-plan__price">
                <Amount paise={course.price_paise} className="amount-chip--plain" />
                <span className="price__period">
                  {course.access_days
                    ? `for ${course.access_days} days of access`
                    : 'one payment, permanent access'}
                </span>
              </div>

              <dl className="definition-list">
                <dt>Lessons</dt>
                <dd>{course.topic_count}</dd>
                <dt>Assessments</dt>
                <dd>{course.task_count}</dd>
                <dt>Rewards available</dt>
                <dd>{formatPaise(course.total_reward)}</dd>
                <dt>Level</dt>
                <dd>{LEVEL_LABELS[course.level] ?? course.level}</dd>
                {duration ? (
                  <>
                    <dt>Length</dt>
                    <dd>{duration}</dd>
                  </>
                ) : null}
              </dl>

              <Alert>{problem}</Alert>

              {order ? (
                <div className="stack">
                  <Alert tone="info">
                    {testGateway
                      ? 'This server uses the built-in test gateway, so no real money moves. The confirmation below still runs through the same signature check the live gateway uses.'
                      : 'Complete the payment in the provider’s window. The course opens as soon as the provider confirms it.'}
                  </Alert>

                  <dl className="definition-list">
                    <dt>Order</dt>
                    <dd>{order.order_id}</dd>
                    <dt>Amount</dt>
                    <dd>{formatPaise(order.amount_paise)}</dd>
                  </dl>

                  <div className="form-actions">
                    {testGateway ? (
                      <Button onClick={confirmPayment} disabled={busy}>
                        {busy ? 'Confirming…' : 'Confirm the test payment'}
                      </Button>
                    ) : null}
                    <Button variant="ghost" onClick={() => setOrder(null)} disabled={busy}>
                      Cancel this payment
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="form-actions">
                  <Button block onClick={startPayment} disabled={busy}>
                    {busy
                      ? 'Contacting the payment provider…'
                      : `Pay ${formatRupees(course.price_paise)}`}
                  </Button>
                </div>
              )}
            </section>
          )}
        </div>

        <aside className="sub-side">
          <section className="card">
            <h2 className="card__title">How this works</h2>
            <ul className="prose__list">
              <li>You select the course and start the payment.</li>
              <li>The payment provider confirms it with a signed callback.</li>
              <li>The server verifies that callback, records the payment and opens the course.</li>
              <li>Closing the tab is safe: the course opens by itself.</li>
            </ul>
          </section>

          <section className="card">
            <h2 className="card__title">What you get</h2>
            <ul className="prose__list">
              <li>All {course.topic_count} lessons, with their notes and videos.</li>
              <li>All {course.task_count} graded assessments.</li>
              <li>Rewards keep paying on every pass.</li>
              <li>
                {course.access_days
                  ? `${course.access_days} days of access, counted from the day you pay.`
                  : 'Access that does not expire.'}
              </li>
            </ul>
          </section>

          <section className="card">
            <h2 className="card__title">What this is not</h2>
            <p className="card__subtitle">
              Not a subscription. It opens this course only, and it neither extends a subscription
              nor pays for any other course.
            </p>
          </section>
        </aside>
      </div>
    </div>
  )
}

export default CourseCheckoutPage
