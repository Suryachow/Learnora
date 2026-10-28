import { useCallback, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { fetchMyAttempts } from '../api/attempts'
import { fetchCourses } from '../api/catalog'
import { fetchMyProgress } from '../api/progress'
import { fetchWallet } from '../api/wallet'
import { Icon } from '../components/Icon'
import useFetch from '../hooks/useFetch'
import { useAuth } from '../hooks/useAuth'
import { formatDateTime, parseUtc } from '../utils/datetime'
import { formatRupees, formatSignedPaise } from '../utils/money'
import '../styles/dashboard.css'

/* ---------------------------------------------------------------------------
   Series helpers. Everything on this page is derived from the ledger and the
   attempt history, so no number here is invented.
   --------------------------------------------------------------------------- */

function dayKey(date) {
  return `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`
}

/** Buckets `items` into `days` local days ending today. */
function dailySeries(items, days, read) {
  const today = new Date()
  const start = new Date(today.getFullYear(), today.getMonth(), today.getDate() - (days - 1))
  const buckets = Array.from({ length: days }, (_, index) => {
    const date = new Date(start.getFullYear(), start.getMonth(), start.getDate() + index)
    return { key: dayKey(date), date, value: 0 }
  })
  const byKey = new Map(buckets.map((bucket) => [bucket.key, bucket]))

  for (const item of items) {
    const date = parseUtc(item.created_at)
    if (!date) continue
    const bucket = byKey.get(dayKey(date))
    if (bucket) bucket.value += read(item) || 0
  }
  return buckets
}

function runningTotal(series) {
  let total = 0
  return series.map((point) => ({ ...point, value: (total += point.value) }))
}

function sumOf(series) {
  return series.reduce((total, point) => total + point.value, 0)
}

/** A smooth cubic path through the points, which is what the reference uses. */
function smoothPath(points) {
  if (points.length === 0) return ''
  if (points.length === 1) return `M ${points[0][0]} ${points[0][1]}`
  let path = `M ${points[0][0]} ${points[0][1]}`
  for (let index = 1; index < points.length; index += 1) {
    const [x0, y0] = points[index - 1]
    const [x1, y1] = points[index]
    const middle = (x0 + x1) / 2
    path += ` C ${middle} ${y0}, ${middle} ${y1}, ${x1} ${y1}`
  }
  return path
}

function Sparkline({ values, variant = 'line' }) {
  const width = 92
  const height = 36
  const max = Math.max(...values, 1)

  if (variant === 'bars') {
    const gap = 3
    const barWidth = (width - gap * (values.length - 1)) / values.length
    return (
      <svg className="lr-kpi__spark" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" aria-hidden="true">
        {values.map((value, index) => {
          const barHeight = Math.max(3, (value / max) * height)
          return (
            <rect
              key={index}
              x={index * (barWidth + gap)}
              y={height - barHeight}
              width={barWidth}
              height={barHeight}
              rx="1.6"
              fill="currentColor"
            />
          )
        })}
      </svg>
    )
  }

  const points = values.map((value, index) => [
    (index / Math.max(values.length - 1, 1)) * width,
    height - 3 - (value / max) * (height - 6),
  ])

  return (
    <svg className="lr-kpi__spark" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" aria-hidden="true">
      <path
        d={smoothPath(points)}
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  )
}

function ActivityChart({ series, format }) {
  const width = 640
  const height = 168
  const top = 12
  const bottom = 8
  const innerHeight = height - top - bottom
  const innerBottom = top + innerHeight
  const max = Math.max(...series.map((point) => point.value), 1)
  /* The 24px of horizontal headroom keeps the value tag inside the card. */
  const points = series.map((point, index) => [
    (index / Math.max(series.length - 1, 1)) * (width - 48) + 24,
    top + innerHeight - (point.value / max) * innerHeight,
  ])
  const line = smoothPath(points)
  const area = `${line} L ${width - 24} ${innerBottom} L 24 ${innerBottom} Z`
  const last = points[points.length - 1] ?? [0, height]
  const labelStep = series.length > 10 ? 5 : 1

  return (
    <div className="lr-chart__wrap">
      <div className="lr-chart__plot">
        <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" aria-hidden="true">
          <defs>
            <linearGradient id="lr-area" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="currentColor" stopOpacity="0.16" />
              <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
            </linearGradient>
          </defs>
          {[0.25, 0.5, 0.75].map((ratio) => (
            <line
              key={ratio}
              className="lr-chart__grid"
              x1="0"
              x2={width}
              y1={top + innerHeight * ratio}
              y2={top + innerHeight * ratio}
            />
          ))}
          <path d={area} fill="url(#lr-area)" />
          <path className="lr-chart__line" d={line} />
        </svg>
        <span
          className="lr-chart__marker"
          style={{ left: `${(last[0] / width) * 100}%`, top: `${(last[1] / height) * 100}%` }}
        />
        <span
          className="lr-chart__tag"
          style={{ left: `${(last[0] / width) * 100}%`, top: `${(last[1] / height) * 100}%` }}
        >
          {format(series[series.length - 1]?.value ?? 0)}
        </span>
      </div>
      <div className="lr-chart__labels">
        {series.map((point, index) => (
          <span key={point.key} style={{ visibility: index % labelStep === 0 || index === series.length - 1 ? 'visible' : 'hidden' }}>
            {point.date.toLocaleDateString(undefined, series.length > 10 ? { day: 'numeric' } : { weekday: 'short' })}
          </span>
        ))}
      </div>
    </div>
  )
}

function DeltaChip({ current, previous }) {
  if (!previous) {
    return current > 0 ? <span className="lr-chip lr-chip--pos">New</span> : null
  }
  const change = Math.round(((current - previous) / previous) * 100)
  return (
    <span className={`lr-chip lr-chip--${change >= 0 ? 'pos' : 'neg'}`}>
      {change >= 0 ? '↑' : '↓'} {Math.abs(change)}%
    </span>
  )
}

function Ring({ percent }) {
  const size = 132
  const stroke = 10
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const filled = (Math.max(0, Math.min(100, percent)) / 100) * circumference

  return (
    <div className="lr-ring">
      <svg viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
        <circle className="lr-ring__track" cx={size / 2} cy={size / 2} r={radius} fill="none" strokeWidth={stroke} />
        <circle
          className="lr-ring__fill"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${filled} ${circumference - filled}`}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      <div className="lr-ring__label">
        <strong>{percent}%</strong>
        <span>passed</span>
      </div>
    </div>
  )
}

const THUMB_TONES = ['#5c7b63', '#4a5b7a', '#7a5b6b', '#8a6d0b', '#3f6b6b', '#6b5b8a']

function thumbTone(text) {
  let hash = 0
  for (let index = 0; index < text.length; index += 1) hash = (hash + text.charCodeAt(index) * (index + 7)) % 997
  return THUMB_TONES[hash % THUMB_TONES.length]
}

const KIND_LABEL = {
  reward: 'Reward',
  subscription: 'Subscription',
  withdrawal: 'Withdrawal',
  course_purchase: 'Course purchase',
  course_payment: 'Course payment',
}

const STATUS_TONE = {
  completed: 'pos',
  pending: 'ghost',
  failed: 'neg',
}

/* ---------------------------------------------------------------------------
   The page.
   --------------------------------------------------------------------------- */

export function DashboardPage() {
  const { user } = useAuth()
  const [range, setRange] = useState('7d')

  const loadCourses = useCallback(() => fetchCourses(), [])
  const loadWallet = useCallback(() => fetchWallet({ limit: 50 }), [])
  const loadProgress = useCallback(() => fetchMyProgress(), [])
  const loadAttempts = useCallback(() => fetchMyAttempts({ limit: 100 }), [])

  const { data: courses, loading: coursesLoading, error: coursesError } = useFetch(loadCourses)
  const { data: wallet } = useFetch(loadWallet)
  const { data: progress } = useFetch(loadProgress)
  const { data: attempts } = useFetch(loadAttempts)

  const days = range === '7d' ? 7 : 30
  const transactions = useMemo(() => wallet?.transactions?.items ?? [], [wallet])
  const attemptList = useMemo(() => attempts?.items ?? [], [attempts])

  /* Rewards are money: only completed ledger rows count. */
  const rewardSeries = useMemo(
    () => dailySeries(transactions, days * 2, (item) => (item.kind === 'reward' && item.status === 'completed' ? item.amount : 0)),
    [transactions, days],
  )
  const attemptSeries = useMemo(() => dailySeries(attemptList, days * 2, () => 1), [attemptList, days])
  const passSeries = useMemo(() => dailySeries(attemptList, days * 2, (item) => (item.passed ? 1 : 0)), [attemptList, days])

  const rewardWindow = rewardSeries.slice(days)
  const rewardPrevious = rewardSeries.slice(0, days)
  const attemptWindow = attemptSeries.slice(days)
  const attemptPrevious = attemptSeries.slice(0, days)
  const passWindow = passSeries.slice(days)

  const earnedInWindow = sumOf(rewardWindow)
  const earnedBefore = sumOf(rewardPrevious)
  const chartSeries = runningTotal(rewardWindow)

  const passed = attemptList.filter((attempt) => attempt.passed).length
  const sample = attemptList.length
  const passRate = sample ? Math.round((passed / sample) * 100) : 0

  const firstName = user.name.trim().split(' ')[0] || 'there'
  const initial = user.name.trim().charAt(0).toUpperCase() || 'U'
  const recentTransactions = transactions.slice(0, 4)

  return (
    <div className="lr-dash">
      <header className="page-header">
        <h1>Hey, {firstName}!</h1>
        <p>Explore your learning activity, assessments and rewards.</p>
      </header>

      <div className="lr-main">
        <div className="lr-content">
          {coursesError ? <p className="lr-alert">{coursesError.message}</p> : null}
          {coursesLoading && !courses ? <p className="lr-notice">Syncing your dashboard…</p> : null}

          <section className="lr-kpis" aria-label="Key numbers" data-stagger>
            <article className="lr-kpi">
              <div className="lr-kpi__head">
                <span className="lr-kpi__label">Rewards earned</span>
                <DeltaChip current={earnedInWindow} previous={earnedBefore} />
              </div>
              <div className="lr-kpi__body">
                <span className="lr-kpi__value">{formatRupees(earnedInWindow)}</span>
                <Sparkline values={rewardWindow.map((point) => point.value)} variant="bars" />
              </div>
              <span className="lr-kpi__foot">Lifetime {formatRupees(wallet?.lifetime_earned_paise ?? 0)}</span>
            </article>

            <article className="lr-kpi">
              <div className="lr-kpi__head">
                <span className="lr-kpi__label">Assessments taken</span>
                <span className="lr-chip lr-chip--ghost">{range === '7d' ? '7 days' : '30 days'}</span>
              </div>
              <div className="lr-kpi__body">
                <div className="lr-kpi__icon">
                  <Icon name="user" />
                </div>
                <span className="lr-kpi__value">{sumOf(attemptWindow)}</span>
                <Sparkline values={attemptWindow.map((point) => point.value)} />
              </div>
              <span className="lr-kpi__foot">{progress?.videos_completed ?? 0} lessons watched in total</span>
            </article>

            <article className="lr-kpi">
              <div className="lr-kpi__head">
                <span className="lr-kpi__label">Assessments passed</span>
                <span className="lr-chip lr-chip--ghost">{passRate}% rate</span>
              </div>
              <div className="lr-kpi__body">
                <div className="lr-kpi__icon is-peach">
                  <Icon name="flame" />
                </div>
                <span className="lr-kpi__value">{passed}</span>
                <Sparkline values={passWindow.map((point) => point.value)} />
              </div>
              <span className="lr-kpi__foot">One reward per task, paid once</span>
            </article>

            <article className="lr-kpi lr-kpi--green">
              <div className="lr-kpi__head">
                <span className="lr-kpi__label">Wallet balance</span>
                <span className="lr-chip lr-chip--green">Ledger-backed</span>
              </div>
              <div className="lr-kpi__body">
                <span className="lr-kpi__value">{formatRupees(wallet?.balance_paise ?? 0)}</span>
                <Sparkline values={chartSeries.map((point) => point.value)} />
              </div>
              <span className="lr-kpi__foot">Computed from every ledger row</span>
            </article>
          </section>

          <div className="lr-grid" data-stagger>
            <section className="lr-card lr-activity">
              <div className="lr-card__head">
                <div>
                  <h2 className="lr-card__title">Learning activity</h2>
                  <span className="lr-card__sub">Rewards that landed, day by day</span>
                </div>
                <div className="lr-card__tools">
                  <span className="lr-chip lr-chip--ghost">{passRate >= 60 ? '✓ On track' : 'In progress'}</span>
                  <div className="lr-seg" role="group" aria-label="Chart range">
                    {[
                      ['7d', 'Weekly'],
                      ['30d', 'Monthly'],
                    ].map(([value, label]) => (
                      <button
                        key={value}
                        className={range === value ? 'is-active' : ''}
                        type="button"
                        onClick={() => setRange(value)}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div className="lr-figures">
                <div className="lr-figure">
                  <span>Rewards earned</span>
                  <div>
                    <strong>{formatRupees(earnedInWindow)}</strong>
                    <DeltaChip current={earnedInWindow} previous={earnedBefore} />
                  </div>
                </div>
                <div className="lr-figure">
                  <span>Assessments</span>
                  <div>
                    <strong>{sumOf(attemptWindow)}</strong>
                    <DeltaChip current={sumOf(attemptWindow)} previous={sumOf(attemptPrevious)} />
                  </div>
                </div>
              </div>

              <div className="lr-chart">
                <ActivityChart series={chartSeries} format={(value) => formatRupees(value)} />
              </div>

              <div className="lr-activity__foot">
                <Link className="lr-btn lr-btn--dark" to="/courses">
                  Continue learning <Icon name="arrow" />
                </Link>
                <p className="lr-activity__note">
                  Rewards are funded by subscriptions, so the platform only pays what it can cover.
                </p>
              </div>
            </section>

            <section className="lr-card lr-rate">
              <div className="lr-card__head">
                <div>
                  <h2 className="lr-card__title">Pass rate</h2>
                  <span className="lr-card__sub">All assessments</span>
                </div>
              </div>
              <div className="lr-rate__body">
                <Ring percent={passRate} />
              </div>
              <p className="lr-rate__foot">
                {passed} of {sample} attempts passed. Grading happens on the server.
              </p>
            </section>

            <section className="lr-card lr-profile">
              <div className="lr-profile__avatar">{initial}</div>
              <h2 className="lr-profile__name">{user.name}</h2>
              <p className="lr-profile__mail">{user.email}</p>
              <div className="lr-profile__stats">
                <div>
                  <span>Courses</span>
                  <strong>{courses?.length ?? 0}</strong>
                </div>
                <div>
                  <span>Lessons</span>
                  <strong>{progress?.videos_completed ?? 0}</strong>
                </div>
                <div>
                  <span>Passed</span>
                  <strong>{passed}</strong>
                </div>
              </div>
            </section>

            <section className="lr-card lr-reward">
              <div className="lr-card__head">
                <div>
                  <h2 className="lr-card__title">Rewards wallet</h2>
                  <span className="lr-card__sub">Available balance</span>
                </div>
                {(wallet?.pending_paise ?? 0) > 0 ? (
                  <span className="lr-chip lr-chip--money">{formatRupees(wallet.pending_paise)} pending</span>
                ) : null}
              </div>
              <div className="lr-walletcard">
                <div className="lr-walletcard__face">
                  <span className="lr-walletcard__brand">LEARNORA</span>
                  <span className="lr-walletcard__chip" />
                  <span className="lr-walletcard__num">•••• •••• •••• 2026</span>
                  <span className="lr-walletcard__foot">
                    <span>Reward wallet</span>
                    <strong>{formatRupees(wallet?.balance_paise ?? 0)}</strong>
                  </span>
                </div>
              </div>
              <Link className="lr-btn lr-btn--dark lr-btn--block" to="/wallet">
                Open wallet <Icon name="arrow" />
              </Link>
            </section>

            <section className="lr-card lr-recent">
              <div className="lr-card__head">
                <div>
                  <h2 className="lr-card__title">Recent transactions</h2>
                  <span className="lr-card__sub">Every reward and payment, newest first</span>
                </div>
                <Link className="lr-card__link" to="/transactions">
                  View all
                </Link>
              </div>

              {recentTransactions.length === 0 ? (
                <p className="lr-empty">Nothing in the ledger yet — pass an assessment to earn your first reward.</p>
              ) : (
                recentTransactions.map((transaction) => (
                  <article className="lr-tx" key={transaction.id}>
                    <span className={`lr-tx__avatar is-${transaction.kind}`}>
                      <Icon name={transaction.kind === 'reward' ? 'coins' : transaction.kind === 'subscription' ? 'trend' : 'arrow'} />
                    </span>
                    <span className="lr-tx__copy">
                      <strong>{transaction.note || KIND_LABEL[transaction.kind] || 'Transaction'}</strong>
                      <small>{formatDateTime(transaction.created_at)}</small>
                    </span>
                    <span className={`lr-chip lr-chip--${STATUS_TONE[transaction.status] ?? 'ghost'}`}>
                      {transaction.status}
                    </span>
                    <strong className={`lr-tx__amount${transaction.amount > 0 ? ' is-pos' : ''}`}>
                      {formatSignedPaise(transaction.amount)}
                    </strong>
                  </article>
                ))
              )}
            </section>

            <section className="lr-card lr-secure">
              <span className="lr-secure__icon">
                <Icon name="shield" />
              </span>
              <h2 className="lr-card__title">Rewards you can trust</h2>
              <p>
                Each pass writes one permanent ledger row. Your balance is calculated from it, never stored as a
                number that can drift.
              </p>
              <Link className="lr-btn lr-btn--ghost" to="/rewards-policy">
                How rewards work
              </Link>
            </section>

            <section className="lr-card lr-courses">
              <div className="lr-card__head">
                <div>
                  <h2 className="lr-card__title">Courses</h2>
                  <span className="lr-card__sub">
                    {courses?.length ?? 0} courses in the catalogue
                  </span>
                </div>
                <Link className="lr-card__link" to="/courses">
                  Browse catalogue
                </Link>
              </div>

              <div className="lr-table">
                <div className="lr-table__head" aria-hidden="true">
                  <span>Course</span>
                  <span>Category</span>
                  <span>Topics</span>
                  <span>Assessments</span>
                  <span>Reward</span>
                  <span />
                </div>
                {(courses ?? []).slice(0, 6).map((course) => (
                  <Link className="lr-table__row" key={course.id} to={`/courses/${course.id}`}>
                    <span className="lr-table__course">
                      <span className="lr-table__thumb" style={{ background: thumbTone(course.category) }}>
                        {course.category.slice(0, 1)}
                      </span>
                      <span className="lr-table__name">
                        {course.title}
                        <small>{course.description}</small>
                      </span>
                    </span>
                    <span className="lr-table__cell">{course.category}</span>
                    <span className="lr-table__cell">{course.topic_count}</span>
                    <span className="lr-table__cell">{course.task_count}</span>
                    <span className="lr-table__money">{formatRupees(course.total_reward)}</span>
                    <span className="lr-table__open">
                      <Icon name="arrow" />
                    </span>
                  </Link>
                ))}
                {(courses ?? []).length === 0 ? <p className="lr-empty">No courses published yet.</p> : null}
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DashboardPage
