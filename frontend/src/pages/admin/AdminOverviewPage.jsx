import { useCallback, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { fetchOverview } from '../../api/admin'
import Alert from '../../components/Alert'
import { Icon } from '../../components/Icon'
import { Loading } from '../../components/Spinner'
import useFetch from '../../hooks/useFetch'
import { formatDateTime } from '../../utils/datetime'
import { formatPaise, formatRupees } from '../../utils/money'
import '../../styles/admin.css'

const PERIODS = [7, 14, 30]

/** Percent change against the previous window, or a plain "no change"/"new" note. */
function deltaOf(current, previous) {
  if (!previous) return current > 0 ? { label: 'new', tone: 'up' } : { label: 'no change', tone: 'flat' }
  const change = ((current - previous) / previous) * 100
  if (Math.abs(change) < 0.05) return { label: 'no change', tone: 'flat' }
  return {
    label: `${change > 0 ? '+' : '−'}${Math.abs(change).toFixed(0)}%`,
    tone: change > 0 ? 'up' : 'down',
  }
}

function Delta({ current, previous, caption = 'vs prev 30 days' }) {
  const delta = deltaOf(current, previous)
  return (
    <p className="ad-delta">
      <span className={`ad-delta__value ad-delta__value--${delta.tone}`}>
        {delta.tone === 'up' ? '↑' : delta.tone === 'down' ? '↓' : '·'} {delta.label}
      </span>
      <span className="ad-delta__caption">{caption}</span>
    </p>
  )
}

/** A 120×32 trend line, scaled to its own max so small series stay readable. */
function Sparkline({ values, tone = 'rev' }) {
  const width = 120
  const height = 32
  const max = Math.max(1, ...values)
  const step = values.length > 1 ? width / (values.length - 1) : width
  const points = values.map((value, index) => {
    const x = index * step
    const y = height - (value / max) * (height - 6) - 3
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })
  return (
    <svg className={`ad-spark ad-spark--${tone}`} viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
      <polyline points={points.join(' ')} fill="none" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function Kpi({ label, value, hint, delta, spark, tone = 'ink' }) {
  return (
    <article className={`ad-kpi ad-kpi--${tone}`}>
      <p className="ad-kpi__label">{label}</p>
      <p className="ad-kpi__value">{value}</p>
      {delta ? <Delta {...delta} /> : null}
      <div className="ad-kpi__foot">
        {hint ? <span className="ad-kpi__hint">{hint}</span> : <span />}
        {spark ? <Sparkline values={spark.values} tone={spark.tone} /> : null}
      </div>
    </article>
  )
}

function axisPath(values, width, height) {
  const max = Math.max(1, ...values)
  const step = values.length > 1 ? width / (values.length - 1) : width
  return values
    .map((value, index) => {
      const x = index * step
      const y = height - (value / max) * (height - 10) - 5
      return `${index === 0 ? 'M' : 'L'}${x.toFixed(1)} ${y.toFixed(1)}`
    })
    .join(' ')
}

function MoneyChart({ daily, period }) {
  const series = daily.slice(-period)
  const width = 720
  const height = 210
  const revenue = series.map((day) => day.revenue_paise)
  const rewards = series.map((day) => day.rewards_paise)
  const totalRevenue = revenue.reduce((sum, value) => sum + value, 0)
  const totalRewards = rewards.reduce((sum, value) => sum + value, 0)
  const peak = Math.max(1, ...revenue, ...rewards)

  const revenueLine = axisPath(revenue, width, height)
  const rewardsLine = axisPath(rewards, width, height)
  const revenueArea = `${revenueLine} L${width} ${height} L0 ${height} Z`
  const rewardsArea = `${rewardsLine} L${width} ${height} L0 ${height} Z`

  return (
    <section className="ad-card ad-card--chart">
      <header className="ad-card__head">
        <div>
          <h2 className="ad-card__title">Money in, rewards out</h2>
          <p className="ad-card__sub">Subscription revenue against completed reward payouts.</p>
        </div>
        <div className="ad-legend">
          <span className="ad-legend__item ad-legend__item--rev">{formatRupees(totalRevenue)} in</span>
          <span className="ad-legend__item ad-legend__item--rew">{formatRupees(totalRewards)} out</span>
        </div>
      </header>

      <div className="ad-chart">
        <span className="ad-chart__axis ad-chart__axis--top">{formatRupees(peak)}</span>
        <span className="ad-chart__axis ad-chart__axis--mid">{formatRupees(peak / 2)}</span>
        <span className="ad-chart__axis ad-chart__axis--base">₹0</span>
        <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`Revenue and rewards over the last ${period} days`}>
          <defs>
            <linearGradient id="ad-rev-fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" style={{ stopColor: 'var(--lr-green)', stopOpacity: 0.26 }} />
              <stop offset="100%" style={{ stopColor: 'var(--lr-green)', stopOpacity: 0 }} />
            </linearGradient>
            <linearGradient id="ad-rew-fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" style={{ stopColor: 'var(--lr-gold)', stopOpacity: 0.24 }} />
              <stop offset="100%" style={{ stopColor: 'var(--lr-gold)', stopOpacity: 0 }} />
            </linearGradient>
          </defs>
          {[0.25, 0.5, 0.75].map((fraction) => (
            <line
              key={fraction}
              className="ad-chart__grid"
              x1="0"
              x2={width}
              y1={height * fraction}
              y2={height * fraction}
            />
          ))}
          <path d={revenueArea} fill="url(#ad-rev-fill)" />
          <path d={rewardsArea} fill="url(#ad-rew-fill)" />
          <path d={revenueLine} className="ad-chart__line ad-chart__line--rev" />
          <path d={rewardsLine} className="ad-chart__line ad-chart__line--rew" />
          {series.map((day, index) => {
            const stepX = series.length > 1 ? width / (series.length - 1) : width
            const y = height - (day.revenue_paise / peak) * (height - 10) - 5
            return (
              <circle key={day.day} className="ad-chart__dot" cx={index * stepX} cy={y} r="2.6">
                <title>{`${day.day} · ${formatPaise(day.revenue_paise)} in · ${formatPaise(day.rewards_paise)} out`}</title>
              </circle>
            )
          })}
        </svg>
        {totalRevenue === 0 && totalRewards === 0 ? (
          <p className="ad-chart__empty">No subscription revenue or payouts recorded in this window yet.</p>
        ) : null}
      </div>

      <footer className="ad-chart__labels">
        <span>{series[0]?.day.slice(5)}</span>
        <span>{series[Math.floor(series.length / 3)]?.day.slice(5)}</span>
        <span>{series[Math.floor((series.length * 2) / 3)]?.day.slice(5)}</span>
        <span>{series[series.length - 1]?.day.slice(5)}</span>
      </footer>
    </section>
  )
}

function RatioCard({ percent, threshold, rewardsToday }) {
  const safePercent = Math.min(100, Math.max(0, percent))
  const over = percent > threshold
  return (
    <section className="ad-card ad-card--ratio">
      <header className="ad-card__head">
        <div>
          <h2 className="ad-card__title">Reward ratio</h2>
          <p className="ad-card__sub">Payouts as a share of subscription revenue.</p>
        </div>
        <span className={`ad-pill ${over ? 'ad-pill--danger' : 'ad-pill--ok'}`}>
          {over ? 'Over threshold' : 'Healthy'}
        </span>
      </header>

      <div className="ad-ring">
        <svg viewBox="0 0 128 128" role="img" aria-label={`${percent.toFixed(1)} percent of revenue paid out as rewards`}>
          <circle className="ad-ring__track" cx="64" cy="64" r="52" />
          <circle
            className={`ad-ring__value ${over ? 'ad-ring__value--danger' : ''}`}
            cx="64"
            cy="64"
            r="52"
            strokeDasharray={`${(safePercent / 100) * 326.7} 326.7`}
          />
        </svg>
        <div className="ad-ring__center">
          <strong>{percent.toFixed(1)}%</strong>
          <span>of revenue</span>
        </div>
      </div>

      <dl className="ad-facts">
        <div>
          <dt>Threshold</dt>
          <dd>{threshold}%</dd>
        </div>
        <div>
          <dt>Paid today</dt>
          <dd>{formatPaise(rewardsToday)}</dd>
        </div>
      </dl>
    </section>
  )
}

function FunnelCard({ steps }) {
  const top = Math.max(1, ...steps.map((step) => step.count))
  return (
    <section className="ad-card ad-card--funnel">
      <header className="ad-card__head">
        <div>
          <h2 className="ad-card__title">Learner funnel</h2>
          <p className="ad-card__sub">From finished video to passed quiz.</p>
        </div>
      </header>
      <ol className="ad-funnel">
        {steps.map((step, index) => {
          const previous = index > 0 ? steps[index - 1].count : null
          const conversion = previous ? Math.round((step.count / previous) * 100) : null
          return (
            <li key={step.label}>
              <div className="ad-funnel__row">
                <span className="ad-funnel__label">{step.label}</span>
                <span className="ad-funnel__count">{step.count.toLocaleString('en-IN')}</span>
              </div>
              <div className="ad-funnel__track">
                <span style={{ width: `${Math.max(step.count ? 4 : 0, (step.count / top) * 100)}%` }} />
              </div>
              {conversion !== null ? (
                <span className="ad-funnel__meta">{conversion}% of the step above</span>
              ) : (
                <span className="ad-funnel__meta">Top of the funnel</span>
              )}
            </li>
          )
        })}
      </ol>
    </section>
  )
}

function TopCoursesCard({ courses }) {
  return (
    <section className="ad-card ad-card--table">
      <header className="ad-card__head">
        <div>
          <h2 className="ad-card__title">Courses carrying the platform</h2>
          <p className="ad-card__sub">Ranked by quiz attempts, with the pass rate behind them.</p>
        </div>
        <Link className="ad-link" to="/admin/courses">
          Manage catalogue
        </Link>
      </header>

      {courses.length ? (
        <div className="ad-table-wrap">
          <table className="ad-table">
            <thead>
              <tr>
                <th scope="col">Course</th>
                <th scope="col">Learners</th>
                <th scope="col">Attempts</th>
                <th scope="col">Pass rate</th>
                <th scope="col">Rewards</th>
              </tr>
            </thead>
            <tbody>
              {courses.map((course) => {
                const rate = course.attempts ? Math.round((course.passed / course.attempts) * 100) : 0
                return (
                  <tr key={course.id}>
                    <td>
                      <span className="ad-table__title">{course.title}</span>
                      <span className="ad-table__meta">{course.category}</span>
                    </td>
                    <td>{course.learners}</td>
                    <td>{course.attempts}</td>
                    <td>
                      <div className="ad-meter">
                        <span style={{ width: `${rate}%` }} />
                      </div>
                      <span className="ad-table__meta">{rate}%</span>
                    </td>
                    <td>{formatRupees(course.rewards_paise)}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="ad-empty">No quiz attempts yet. Once learners start, the strongest courses surface here.</p>
      )}
    </section>
  )
}

function initials(name) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join('')
}

function AttemptsCard({ attempts }) {
  return (
    <section className="ad-card">
      <header className="ad-card__head">
        <div>
          <h2 className="ad-card__title">Latest quiz runs</h2>
          <p className="ad-card__sub">Server-graded, newest first.</p>
        </div>
        <Link className="ad-link" to="/admin/users">
          All learners
        </Link>
      </header>

      {attempts.length ? (
        <ul className="ad-feed">
          {attempts.map((attempt) => (
            <li key={attempt.id}>
              <span className="ad-avatar" aria-hidden="true">{initials(attempt.user_name)}</span>
              <div className="ad-feed__body">
                <p>
                  <strong>{attempt.user_name}</strong> {attempt.passed ? 'passed' : 'sat'}{' '}
                  <span>{attempt.task_title}</span>
                </p>
                <span className="ad-feed__meta">
                  {attempt.course_title} · {formatDateTime(attempt.created_at)}
                </span>
              </div>
              <span className={`ad-score ${attempt.passed ? 'ad-score--ok' : 'ad-score--miss'}`}>
                {attempt.percent}%
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="ad-empty">No quiz runs yet.</p>
      )}
    </section>
  )
}

function EarnersCard({ learners }) {
  const top = Math.max(1, ...learners.map((learner) => learner.rewards_paise))
  return (
    <section className="ad-card">
      <header className="ad-card__head">
        <div>
          <h2 className="ad-card__title">Top earners</h2>
          <p className="ad-card__sub">Lifetime rewards from the ledger.</p>
        </div>
      </header>

      {learners.length ? (
        <ul className="ad-earners">
          {learners.map((learner) => (
            <li key={learner.id}>
              <span className="ad-avatar ad-avatar--soft" aria-hidden="true">{initials(learner.name)}</span>
              <div className="ad-earners__body">
                <p>{learner.name}</p>
                <span className="ad-earners__track">
                  <span style={{ width: `${Math.max(6, (learner.rewards_paise / top) * 100)}%` }} />
                </span>
              </div>
              <span className="ad-earners__value">{formatRupees(learner.rewards_paise)}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="ad-empty">Rewards will show up here once learners start passing quizzes.</p>
      )}
    </section>
  )
}

function ActionsCard({ data }) {
  const actions = [
    { to: '/admin/courses', icon: 'book', label: 'Create or edit a course' },
    { to: '/admin/tasks', icon: 'award', label: 'Build a quiz' },
    { to: '/admin/users', icon: 'user', label: 'Grant a subscription' },
    { to: '/admin/settings', icon: 'settings', label: 'Reward policy settings' },
  ]
  return (
    <section className="ad-card ad-card--actions">
      <header className="ad-card__head">
        <div>
          <h2 className="ad-card__title">Console shortcuts</h2>
          <p className="ad-card__sub">The four things you do most.</p>
        </div>
      </header>

      <nav className="ad-actions">
        {actions.map((action) => (
          <Link key={action.to} to={action.to}>
            <span className="ad-actions__icon"><Icon name={action.icon} /></span>
            {action.label}
            <Icon name="arrow" className="ad-actions__arrow" />
          </Link>
        ))}
      </nav>

      <dl className="ad-status">
        <div>
          <dt>Rewards engine</dt>
          <dd>
            <span className={`ad-dot ${data.rewards_enabled ? 'ad-dot--on' : 'ad-dot--off'}`} />
            {data.rewards_enabled ? 'Running' : 'Paused'}
          </dd>
        </div>
        <div>
          <dt>Active learners · 7 days</dt>
          <dd>{data.active_learners_7d}</dd>
        </div>
        <div>
          <dt>Catalogue</dt>
          <dd>{data.course_count} courses · {data.topic_count} topics</dd>
        </div>
        <div>
          <dt>Live tasks</dt>
          <dd>{data.active_task_count} of {data.task_count}</dd>
        </div>
      </dl>
    </section>
  )
}

function OnboardingCard() {
  const steps = [
    { to: '/admin/courses', icon: 'book', title: 'Publish a course', body: 'A course holds the topics, and each topic holds the lesson video.' },
    { to: '/admin/tasks', icon: 'award', title: 'Add an assessment', body: 'Give it a pass mark and a reward — that is what the ledger pays out.' },
    { to: '/admin/users', icon: 'user', title: 'Give a learner access', body: 'Grant a subscription so the first quiz can actually be taken.' },
  ]
  return (
    <section className="ad-onboard">
      <div className="ad-onboard__head">
        <p className="ad-eyebrow">First run</p>
        <h2 className="ad-onboard__title">The console is wired up — it just needs its first cohort</h2>
        <p className="ad-onboard__sub">
          The numbers below fill in the moment someone subscribes or sits a quiz. Three things unlock
          that.
        </p>
      </div>
      <ol className="ad-onboard__steps">
        {steps.map((step, index) => (
          <li key={step.to}>
            <span className="ad-onboard__index">{index + 1}</span>
            <div>
              <Link to={step.to}>{step.title}</Link>
              <p>{step.body}</p>
            </div>
            <Icon name={step.icon} />
          </li>
        ))}
      </ol>
    </section>
  )
}

function LedgerCard({ rows }) {
  return (
    <section className="ad-card">
      <header className="ad-card__head">
        <div>
          <h2 className="ad-card__title">Recent ledger activity</h2>
          <p className="ad-card__sub">Every row is append-only, straight from the wallet ledger.</p>
        </div>
      </header>

      {rows.length ? (
        <div className="ad-table-wrap">
          <table className="ad-table">
            <thead>
              <tr>
                <th scope="col">When</th>
                <th scope="col">Learner</th>
                <th scope="col">Kind</th>
                <th scope="col">Amount</th>
                <th scope="col">Note</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id}>
                  <td>{formatDateTime(row.created_at)}</td>
                  <td>
                    <span className="ad-table__title">{row.user_name}</span>
                    <span className="ad-table__meta">{row.user_email}</span>
                  </td>
                  <td>
                    <span className={`ad-pill ${row.kind === 'reward' ? 'ad-pill--gold' : 'ad-pill--neutral'}`}>
                      {row.kind}
                    </span>
                  </td>
                  <td className={row.amount > 0 ? 'ad-money--in' : 'ad-money--out'}>
                    {formatPaise(row.amount)}
                  </td>
                  <td className="ad-table__note">{row.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="ad-empty">The ledger is empty. Payments and rewards will appear here.</p>
      )}
    </section>
  )
}

/** The admin console home: money, movement and the health of the catalogue. */
export function AdminOverviewPage() {
  const load = useCallback(() => fetchOverview(), [])
  const { data, loading, error, reload } = useFetch(load)
  const [period, setPeriod] = useState(14)

  const { growth, totals } = useMemo(() => {
    if (!data) return { growth: null, totals: null }
    const window = data.daily.slice(-period)
    return {
      growth: data.growth,
      totals: {
        revenue: window.reduce((sum, day) => sum + day.revenue_paise, 0),
        rewards: window.reduce((sum, day) => sum + day.rewards_paise, 0),
        signups: window.map((day) => day.signups),
        attempts: window.map((day) => day.attempts),
      },
    }
  }, [data, period])

  if (loading) return <Loading label="Reading the ledger…" />

  if (error) {
    return (
      <div className="ad">
        <Alert>{error.message}</Alert>
        <button type="button" className="btn btn--secondary" onClick={reload}>
          Try again
        </button>
      </div>
    )
  }

  const today = new Date().toLocaleDateString(undefined, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  })

  return (
    <div className="ad">
      <header className="ad-head">
        <div>
          <p className="ad-eyebrow">Admin console</p>
          <h1 className="ad-title">The platform at a glance</h1>
          <p className="ad-sub">{today} · money in, rewards out, and the learners behind both.</p>
        </div>
        <div className="ad-head__actions">
          <div className="ad-seg" role="group" aria-label="Chart period">
            {PERIODS.map((option) => (
              <button
                key={option}
                type="button"
                aria-pressed={period === option}
                className={period === option ? 'is-active' : ''}
                onClick={() => setPeriod(option)}
              >
                {option}d
              </button>
            ))}
          </div>
          <Link className="btn btn--primary" to="/admin/courses">
            Create course
          </Link>
        </div>
      </header>

      {data.reward_ratio_warning ? (
        <Alert tone="warning">
          Rewards are {data.reward_ratio_percent.toFixed(1)}% of revenue, above your{' '}
          {data.warning_threshold_percent}% threshold. Review the limits in{' '}
          <Link to="/admin/settings">settings</Link>.
        </Alert>
      ) : null}

      {!data.rewards_enabled ? (
        <Alert tone="warning">
          The platform-wide rewards switch is off, so no learner is being paid. Turn it back on in{' '}
          <Link to="/admin/settings">settings</Link>.
        </Alert>
      ) : null}

      {data.total_attempts === 0 ? <OnboardingCard /> : null}

      <div className="ad-kpis" data-stagger>
        <Kpi
          label="Revenue"
          value={formatRupees(data.revenue_paise)}
          hint={`${formatRupees(totals.revenue)} in the last ${period} days`}
          delta={{ current: growth.current.revenue_paise, previous: growth.previous.revenue_paise }}
          spark={{ values: data.daily.slice(-period).map((day) => day.revenue_paise), tone: 'rev' }}
        />
        <Kpi
          label="Rewards paid"
          value={formatRupees(data.rewards_paid_paise)}
          hint={`${data.reward_ratio_percent.toFixed(1)}% of revenue · ${formatRupees(data.rewards_today_paise)} today`}
          delta={{ current: growth.current.rewards_paise, previous: growth.previous.rewards_paise }}
          spark={{ values: data.daily.slice(-period).map((day) => day.rewards_paise), tone: 'rew' }}
          tone="gold"
        />
        <Kpi
          label={`New learners · ${growth.days}d`}
          value={growth.current.signups}
          hint={`${data.total_users} accounts · ${data.subscribed_users} subscribed`}
          delta={{ current: growth.current.signups, previous: growth.previous.signups }}
          spark={{ values: totals.signups, tone: 'rev' }}
        />
        <Kpi
          label="Quiz pass rate"
          value={`${data.pass_rate_percent.toFixed(1)}%`}
          hint={`${data.passed_attempts} of ${data.total_attempts} attempts passed`}
          delta={{ current: growth.current.attempts, previous: growth.previous.attempts, caption: 'attempts vs prev 30 days' }}
          spark={{ values: totals.attempts, tone: 'rew' }}
          tone="sage"
        />
      </div>

      <div className="ad-grid ad-grid--main" data-stagger>
        <MoneyChart daily={data.daily} period={period} />
        <RatioCard
          percent={data.reward_ratio_percent}
          threshold={data.warning_threshold_percent}
          rewardsToday={data.rewards_today_paise}
        />
      </div>

      <div className="ad-grid ad-grid--split" data-stagger>
        <TopCoursesCard courses={data.top_courses} />
        <FunnelCard steps={data.funnel} />
      </div>

      <div className="ad-grid ad-grid--trio" data-stagger>
        <AttemptsCard attempts={data.recent_attempts} />
        <EarnersCard learners={data.top_learners} />
        <ActionsCard data={data} />
      </div>

      <LedgerCard rows={data.recent_transactions} />
    </div>
  )
}

export default AdminOverviewPage
