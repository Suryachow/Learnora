import { useCallback, useMemo, useRef } from 'react'
import { Link } from 'react-router-dom'

import { fetchCourses } from '../api/catalog'
import { fetchPlan } from '../api/subscription'
import { Icon } from '../components/Icon'
import useFetch from '../hooks/useFetch'
import { useReveal } from '../hooks/useReveal'
import { formatRupees } from '../utils/money'
import '../styles/landing.css'

const FEATURED = 3

const STEPS = [
  {
    title: 'Pick a course',
    body: 'Every outline lists its topics, the assessment in each one and what passing pays.',
  },
  {
    title: 'Watch it to the end',
    body: 'The video plays start to finish. Skipping ahead is blocked, and completion only counts at the end.',
  },
  {
    title: 'Check in honestly',
    body: 'A three-way understanding check with room for a note. It is stored against the topic, not averaged away.',
  },
  {
    title: 'Pass and get paid',
    body: 'The assessment is graded on the server. A passing attempt puts the reward in your wallet, once per task.',
  },
]

const FEATURES = [
  {
    icon: 'lock',
    title: 'No skipping, by design',
    body: 'The player pulls you back if you jump ahead, and a lesson only counts as watched when playback actually reaches the end.',
  },
  {
    icon: 'shield',
    title: 'Graded on the server',
    body: 'Quiz answers never reach the browser before you submit, so the score you see is the score that was earned.',
  },
  {
    icon: 'check',
    title: 'Honest check-ins',
    body: 'Not sure, mostly, or confident — plus a note. The gaps you admit to are the ones you can close.',
  },
  {
    icon: 'coins',
    title: 'A ledger you can read',
    body: 'Subscriptions in, rewards out. Every line lives in an append-only ledger you can open from your wallet.',
  },
  {
    icon: 'trend',
    title: 'Progress that means something',
    body: 'Completion is tracked topic by topic, not as a single vanity percentage you can never audit.',
  },
  {
    icon: 'award',
    title: 'Certificates with a trail',
    body: 'A certificate lines up with the assessments behind it. Coursework you skipped never quietly becomes a credential.',
  },
  {
    icon: 'book',
    title: 'Notes beside every video',
    body: 'Written material sits next to the player, so revising a topic does not mean scrubbing through it again.',
  },
  {
    icon: 'settings',
    title: 'Both sides of the desk',
    body: 'Learners get a dashboard. Administrators get a console for courses, tasks, a 30-day report and the rewards switch.',
  },
]

const INCLUDED = [
  'A course library with video lessons and written notes',
  'Completion-gated playback — no skipping ahead',
  'Understanding check-ins with a private note',
  'Server-graded assessments with a per-task pass mark',
  'One reward per task, recorded once in the ledger',
  'A wallet with balance, pending and lifetime totals',
  'Progress tracked topic by topic, not averaged',
  'Certificates tied to work you actually finished',
  'Password changes and a one-tap sign-out on this device',
]

const FAQ = [
  {
    q: 'Do I need a subscription to start?',
    a: 'No. Reading the material and watching lesson videos is free. An active subscription unlocks assessments and the rewards they pay.',
  },
  {
    q: 'Can I skip a video I already know?',
    a: 'You can scrub, but the lesson will not complete until playback reaches the end. Completion is what unlocks the check-in and the quiz.',
  },
  {
    q: 'How are assessments graded?',
    a: 'On the server. Correct answers are never sent to the browser with the questions, and the pass mark is set per task by the course team.',
  },
  {
    q: 'What happens if I fail one?',
    a: 'Nothing is credited. The attempt stays in your history, and you can try again once the cooldown for that task has passed.',
  },
  {
    q: 'When does a reward arrive?',
    a: 'Immediately after a passing attempt, once per task per account. The one-per-task rule is enforced by the database, not the page.',
  },
  {
    q: 'Where do rewards come from?',
    a: 'Subscriptions. Rewards are a share of revenue, not profit, and the percentages can change — the Rewards Policy is the version that counts.',
  },
  {
    q: 'Can rewards be paused?',
    a: 'Yes. If they are, your existing balance is untouched, the switch is visible in your wallet, and the policy page states what applies while they are off.',
  },
]

const PLAN_PERKS = [
  'Every eligible assessment unlocked, across all courses',
  'Rewards credited the moment an attempt passes',
  'Extending early adds days to the end of the period you already paid for',
  'Wallet, certificates and ledger stay yours without a renewal',
]

function Stat({ icon, value, label, tone }) {
  return (
    <div className={`lp-stat ${tone ? `lp-stat--${tone}` : ''}`.trim()}>
      <span className="lp-stat__icon"><Icon name={icon} /></span>
      <span className="lp-stat__body">
        <span className="lp-stat__value">{value}</span>
        <span className="lp-stat__label">{label}</span>
      </span>
    </div>
  )
}

function LessonMock({ course }) {
  return (
    <div className="lp-mock" aria-hidden="true">
      <div className="lp-mock__bar">
        <span className="lp-mock__dot" />
        <span className="lp-mock__dot" />
        <span className="lp-mock__dot" />
        <span className="lp-mock__url">learnora.app/dashboard</span>
        <span className="lp-mock__live">live</span>
      </div>

      <div className="lp-mock__body">
        <div className="lp-mock__lesson">
          <div className="lp-mock__player">
            <span className="lp-mock__play"><Icon name="play" /></span>
            <span className="lp-mock__time">12:04 / 15:20</span>
            <span className="lp-mock__scrub"><span /></span>
          </div>
          <p className="lp-mock__kicker">Topic 3 of 8 · {course?.category ?? 'Catalogue'}</p>
          <p className="lp-mock__title">{course?.title ?? 'Your next course outline'}</p>
          <div className="lp-mock__progress"><span /></div>
          <div className="lp-mock__row">
            <span>Lesson complete</span>
            <strong>64%</strong>
          </div>
        </div>

        <div className="lp-mock__side">
          <div className="lp-mock__chip lp-mock__chip--gold">
            <span className="lp-mock__chip-icon"><Icon name="coins" /></span>
            <span>
              <small>Reward on pass</small>
              <strong>{formatRupees(course?.total_reward ?? 12000)}</strong>
            </span>
          </div>
          <div className="lp-mock__chip">
            <span className="lp-mock__chip-icon"><Icon name="flame" /></span>
            <span>
              <small>Learning streak</small>
              <strong>6 days</strong>
            </span>
          </div>
          <div className="lp-mock__spark">
            {[38, 62, 44, 80, 56, 92, 72].map((height, index) => (
              <span key={index} style={{ height: `${height}%` }} />
            ))}
          </div>
        </div>
      </div>

      <div className="lp-mock__float lp-mock__float--pass">
        <Icon name="check" /> Quiz passed · 92%
      </div>
      <div className="lp-mock__float lp-mock__float--lock">
        <Icon name="lock" /> Quiz unlocked
      </div>
    </div>
  )
}

/** The public front door. Signed-out visitors land here; the dashboard lives at /dashboard. */
export function LandingPage() {
  const loadCourses = useCallback(() => fetchCourses(), [])
  const { data, loading } = useFetch(loadCourses)

  const loadPlan = useCallback(() => fetchPlan(), [])
  const { data: plan, loading: planLoading } = useFetch(loadPlan)

  const revealRef = useReveal()
  const mediaRef = useRef(null)

  const courses = data ?? []

  const { stats, categories, featured } = useMemo(() => {
    const topics = courses.reduce((sum, course) => sum + (course.topic_count ?? 0), 0)
    const reward = courses.reduce((sum, course) => sum + (course.total_reward ?? 0), 0)
    const tracks = [...new Set(courses.map((course) => course.category))].sort()
    return {
      stats: { courses: courses.length, topics, reward },
      categories: tracks.slice(0, 8),
      featured: courses.slice(0, FEATURED),
    }
  }, [courses])

  // The mock leans towards the pointer. Values live on the wrapper so the CSS
  // can compose them with the resting tilt; reduced motion opts out entirely.
  function handlePointerMove(event) {
    const node = mediaRef.current
    if (!node) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const rect = node.getBoundingClientRect()
    const x = (event.clientX - rect.left) / rect.width - 0.5
    const y = (event.clientY - rect.top) / rect.height - 0.5
    node.style.setProperty('--tilt-y', `${(x * 8).toFixed(2)}deg`)
    node.style.setProperty('--tilt-x', `${(-y * 6).toFixed(2)}deg`)
  }

  function resetTilt() {
    const node = mediaRef.current
    if (!node) return
    node.style.setProperty('--tilt-y', '0deg')
    node.style.setProperty('--tilt-x', '0deg')
  }

  return (
    <div className="lp" ref={revealRef}>
      <section className="lp-hero">
        <div className="lp-hero__glow" aria-hidden="true" />

        <div className="lp-hero__copy" data-reveal>
          <span className="lp-badge">
            <span className="lp-badge__dot" />
            Learn a skill · Prove it · Earn rewards
          </span>

          <h1 className="lp-hero__title">
            Finish what you start.
            <br />
            <em>Prove</em> what you learned.
          </h1>

          <p className="lp-hero__lead">
            Learnora pairs every lesson with an honest check-in and a real assessment. Watch the
            video all the way through, say how it landed, then prove it in a quiz — and watch the
            reward land in your wallet.
          </p>

          <div className="lp-hero__cta">
            <Link className="btn btn--primary lp-btn" to="/signup">
              Start learning free
              <Icon name="arrow" />
            </Link>
            <Link className="btn btn--secondary lp-btn" to="/courses">
              Explore the catalogue
            </Link>
          </div>

          <ul className="lp-hero__trust">
            <li><Icon name="play" /> Lessons play start to finish</li>
            <li><Icon name="lock" /> Quizzes unlock after the check-in</li>
            <li><Icon name="coins" /> Every payout sits in an auditable ledger</li>
          </ul>
        </div>

        <div
          className="lp-hero__media"
          ref={mediaRef}
          onPointerMove={handlePointerMove}
          onPointerLeave={resetTilt}
          data-reveal
          style={{ '--reveal-delay': '120ms' }}
        >
          <LessonMock course={featured[0]} />
        </div>
      </section>

      <section className="lp-stats" aria-label="Catalogue at a glance" data-reveal>
        <Stat icon="book" value={stats.courses} label="Courses in the catalogue" />
        <Stat icon="trend" value={stats.topics} label="Topics mapped end to end" />
        <Stat
          icon="coins"
          tone="gold"
          value={formatRupees(stats.reward)}
          label="Rewards available across the catalogue"
        />
        <p className="lp-stats__note">Live from the catalogue, not a marketing figure.</p>
      </section>

      <section className="lp-section" id="how-it-works">
        <header className="lp-head" data-reveal>
          <p className="lp-eyebrow">The loop</p>
          <h2 className="lp-title">One lesson, four honest steps</h2>
          <p className="lp-lead">
            The same routine on every topic, so you always know what comes next — and nothing gets
            marked as done until you have actually done it.
          </p>
        </header>

        <ol className="lp-steps">
          {STEPS.map((step, index) => (
            <li
              key={step.title}
              className="lp-step"
              data-reveal
              style={{ '--reveal-delay': `${index * 70}ms` }}
            >
              <span className="lp-step__number">{String(index + 1).padStart(2, '0')}</span>
              <h3 className="lp-step__title">{step.title}</h3>
              <p className="lp-step__body">{step.body}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="lp-section" id="why">
        <header className="lp-head" data-reveal>
          <p className="lp-eyebrow">What is different</p>
          <h2 className="lp-title">Built for people who want to finish</h2>
          <p className="lp-lead">
            Most platforms hand you a playlist and a tick box. Learnora treats each topic as a small
            closed loop — watch, reflect, prove — so the certificate at the end means something.
          </p>
        </header>

        <div className="lp-features">
          {FEATURES.map((feature, index) => (
            <article
              key={feature.title}
              className="lp-feature"
              data-reveal
              style={{ '--reveal-delay': `${(index % 3) * 60}ms` }}
            >
              <span className="lp-feature__icon"><Icon name={feature.icon} /></span>
              <h3 className="lp-feature__title">{feature.title}</h3>
              <p className="lp-feature__body">{feature.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="lp-section" id="included">
        <header className="lp-head" data-reveal>
          <p className="lp-eyebrow">Included from day one</p>
          <h2 className="lp-title">Everything the loop needs</h2>
          <p className="lp-lead">
            No add-ons and no upsell ladder. One account covers the learning, the proof and the
            record of what you earned.
          </p>
        </header>

        <div className="lp-included">
          <ul className="lp-included__grid">
            {INCLUDED.map((item, index) => (
              <li key={item} data-reveal style={{ '--reveal-delay': `${index * 40}ms` }}>
                <Icon name="check" />
                <span>{item}</span>
              </li>
            ))}
          </ul>

          <aside className="lp-included__panel" data-reveal>
            <p className="lp-included__label">Two sides, one ledger</p>

            <div className="lp-role">
              <span className="lp-role__icon"><Icon name="user" /></span>
              <div>
                <h3 className="lp-role__title">Learner</h3>
                <p className="lp-role__body">
                  Courses, check-ins, assessments, wallet, certificates and a dashboard that shows
                  the next unfinished topic.
                </p>
              </div>
            </div>

            <div className="lp-role">
              <span className="lp-role__icon"><Icon name="settings" /></span>
              <div>
                <h3 className="lp-role__title">Administrator</h3>
                <p className="lp-role__body">
                  Publishes courses and tasks, watches a 30-day earnings report, and can pause
                  rewards platform-wide.
                </p>
              </div>
            </div>

            <p className="lp-included__note">
              Balances are derived from the ledger, never stored — both views read the same rows.
            </p>
          </aside>
        </div>
      </section>

      <section className="lp-section" id="catalogue">
        <header className="lp-head lp-head--row" data-reveal>
          <div>
            <p className="lp-eyebrow">The catalogue</p>
            <h2 className="lp-title">Courses to start with</h2>
            <p className="lp-lead">
              Each card shows what you will cover, how many assessments are inside, and what passing
              them pays.
            </p>
          </div>
          <Link className="btn btn--secondary lp-btn" to="/courses">
            See every course
            <Icon name="arrow" />
          </Link>
        </header>

        {categories.length ? (
          <div className="lp-tags" data-reveal>
            {categories.map((category) => (
              <Link key={category} className="lp-tag" to={`/courses?category=${encodeURIComponent(category)}`}>
                {category}
              </Link>
            ))}
          </div>
        ) : null}

        {loading ? <p className="lp-note">Loading the catalogue…</p> : null}

        {!loading && featured.length === 0 ? (
          <p className="lp-note">
            The catalogue is being set up. Courses appear here as soon as an administrator publishes
            them.
          </p>
        ) : null}

        <div className="lp-courses">
          {featured.map((course, index) => (
            <Link
              key={course.id}
              className="lp-course"
              to={`/courses/${course.id}`}
              data-reveal
              style={{ '--reveal-delay': `${index * 70}ms` }}
            >
              <div className="lp-course__top">
                <span className="lp-course__tag">{course.category}</span>
                <span className="lp-course__arrow"><Icon name="arrow" /></span>
              </div>
              <h3 className="lp-course__title">{course.title}</h3>
              <p className="lp-course__body">{course.description}</p>
              <div className="lp-course__meta">
                <span>{course.topic_count} {course.topic_count === 1 ? 'topic' : 'topics'}</span>
                <span>{course.task_count} {course.task_count === 1 ? 'assessment' : 'assessments'}</span>
                {course.total_reward > 0 ? (
                  <span className="lp-course__reward">{formatRupees(course.total_reward)} to earn</span>
                ) : null}
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="lp-section" id="membership">
        <div className="lp-member" data-reveal>
          <div className="lp-member__main">
            <p className="lp-eyebrow">Membership</p>
            <h2 className="lp-title">One membership, every assessment</h2>
            <p className="lp-lead">
              Watching and reading are free, always. A membership is what unlocks the assessments —
              and every task you pass pays a reward back into the same wallet you can audit.
            </p>
            <ul className="lp-member__list">
              {PLAN_PERKS.map((perk) => (
                <li key={perk}><Icon name="check" /> {perk}</li>
              ))}
            </ul>
            <div className="lp-member__cta">
              <Link className="btn btn--primary lp-btn" to="/signup">
                Create an account to start
                <Icon name="arrow" />
              </Link>
              <Link className="btn btn--secondary lp-btn" to="/rewards-policy">
                Read the rewards policy
              </Link>
            </div>
          </div>

          <aside className="lp-member__card">
            <p className="lp-member__label">{plan?.name ?? 'The plan'}</p>
            {plan ? (
              <>
                <p className="lp-member__price">
                  {formatRupees(plan.price_paise)}
                  <span>for {plan.days} days</span>
                </p>
                <p className="lp-member__desc">{plan.description}</p>
                <dl className="lp-member__facts">
                  <div>
                    <dt>Length</dt>
                    <dd>{plan.days} days</dd>
                  </div>
                  <div>
                    <dt>Currency</dt>
                    <dd>{plan.currency}</dd>
                  </div>
                </dl>
                <p className="lp-member__note">
                  <Icon name="shield" /> One payment, no auto-renewal.
                </p>
                {plan.rewards_enabled ? null : (
                  <p className="lp-member__paused">
                    Rewards are paused platform-wide right now. You can still learn and subscribe —
                    new payouts resume when the switch is back on.
                  </p>
                )}
              </>
            ) : (
              <p className="lp-member__desc">
                {planLoading
                  ? 'Loading the current plan…'
                  : 'The current price is shown on the subscription page once you have an account.'}
              </p>
            )}
            <p className="lp-member__fine">Watching and reading stay free. No card needed to look around.</p>
          </aside>
        </div>
      </section>

      <section className="lp-rewards" id="rewards">
        <div className="lp-rewards__panel" data-reveal>
          <p className="lp-eyebrow lp-eyebrow--light">Rewards, plainly</p>
          <h2 className="lp-title lp-title--light">Money you can trace, line by line</h2>
          <p className="lp-rewards__lead">
            Rewards are funded by subscriptions — a share of revenue, not profit. Every credit and
            debit is written to an append-only ledger, and you can read yours at any time.
          </p>
          <ul className="lp-rewards__list">
            <li><Icon name="check" /> One reward per task per account, enforced by the database</li>
            <li><Icon name="check" /> Quiz grading happens on the server, never in the browser</li>
            <li><Icon name="check" /> Payout rules live in settings, published on the policy page</li>
          </ul>
          <Link className="lp-rewards__link" to="/rewards-policy">
            Read the rewards policy
            <Icon name="arrow" />
          </Link>
        </div>

        <div className="lp-rewards__side">
          {[
            ['wallet', 'Wallet and ledger', 'See every subscription, reward and payout in one running balance.'],
            ['award', 'Certificates you earned', 'A certificate appears only after the assessments behind it were passed.'],
            ['shield', 'Private by default', 'Understanding notes sit against your own progress — they are there for you.'],
          ].map(([icon, title, body], index) => (
            <article
              key={title}
              className="lp-guarantee"
              data-reveal
              style={{ '--reveal-delay': `${index * 70}ms` }}
            >
              <span className="lp-guarantee__icon"><Icon name={icon} /></span>
              <div>
                <h3 className="lp-guarantee__title">{title}</h3>
                <p className="lp-guarantee__body">{body}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="lp-section" id="faq">
        <header className="lp-head" data-reveal>
          <p className="lp-eyebrow">Questions</p>
          <h2 className="lp-title">The things people ask first</h2>
        </header>

        <div className="lp-faq">
          {FAQ.map((item) => (
            <details key={item.q} className="lp-faq__item" data-reveal>
              <summary>
                {item.q}
                <span className="lp-faq__icon"><Icon name="plus" /></span>
              </summary>
              <p>{item.a}</p>
            </details>
          ))}
        </div>
      </section>

      <section className="lp-final" data-reveal>
        <div className="lp-final__glow" aria-hidden="true" />
        <p className="lp-eyebrow">Ready when you are</p>
        <h2 className="lp-title">Finish one course properly this week</h2>
        <p className="lp-lead">
          Create an account, work through your first topic, and see what a completed lesson feels
          like. Watching is free — the assessment is where it counts.
        </p>
        <div className="lp-final__cta">
          <Link className="btn btn--primary lp-btn" to="/signup">
            Create a free account
            <Icon name="arrow" />
          </Link>
          <Link className="btn btn--secondary lp-btn" to="/login">
            I already have one
          </Link>
        </div>
      </section>

      <footer className="lp-footer">
        <div className="lp-footer__brand">
          <span className="lp-footer__mark"><Icon name="spark" /></span>
          <div>
            <p className="lp-footer__name">Learnora</p>
            <p className="lp-footer__tag">Learn a skill, prove it, get rewarded.</p>
          </div>
        </div>

        <nav className="lp-footer__links" aria-label="Footer">
          <div>
            <p className="lp-footer__heading">Learn</p>
            <Link to="/courses">Catalogue</Link>
            <a href="#how-it-works">How it works</a>
            <Link to="/rewards-policy">Rewards policy</Link>
          </div>
          <div>
            <p className="lp-footer__heading">Account</p>
            <Link to="/login">Sign in</Link>
            <Link to="/signup">Create account</Link>
            <Link to="/certificates">Certificates</Link>
          </div>
        </nav>

        <div className="lp-footer__base">
          <span>© {new Date().getFullYear()} Learnora. Built for learners who finish.</span>
          <span>Rewards are funded by subscriptions and are not a return on investment.</span>
        </div>
      </footer>
    </div>
  )
}

export default LandingPage
