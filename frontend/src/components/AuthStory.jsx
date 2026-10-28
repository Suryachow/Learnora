import { Icon } from './Icon'

/** What the pass actually contains, said plainly rather than in slogans. */
const PASS_ROWS = [
  'Notes and video for every lesson',
  'All 18 assessments, graded on the server',
  'Rewards paid every time you pass',
]

const STATS = [
  { value: '2', label: 'courses: C and Python' },
  { value: '38', label: 'lessons, 190 graded questions' },
  { value: '₹5–35', label: 'paid per video or quiz pass' },
]

/**
 * The dark half of the sign-in screen. It shows what a learner is buying - one
 * course pass, every assessment inside it - instead of describing it at length.
 */
export function AuthStory({ mode = 'login' }) {
  const returning = mode === 'login'

  return (
    <section className="auth-story" aria-label="What a Learnora course pass opens">
      <header className="auth-story__head">
        <p className="auth-story__eyebrow">
          {returning ? 'C and Python · one payment each' : 'Free to read · pay once to assess'}
        </p>

        <h2 className="auth-story__title">
          {returning ? 'Pick up where you stopped.' : 'Learn one language properly, then prove it.'}
        </h2>

        <p className="auth-story__lead">
          {returning
            ? 'The loop is the same on every lesson: watch to the end, check in honestly, then pass the assessment. Nothing is marked done until it is done.'
            : 'Reading and watching stay free. A course pass opens every assessment inside it, and each pass pays a reward you can trace.'}
        </p>
      </header>

      <article className="course-pass">
        <div className="course-pass__head">
          <span>Course pass</span>
          <strong>₹349 once</strong>
        </div>

        <div className="course-pass__body">
          <h3 className="course-pass__title">C Programming</h3>
          <p className="course-pass__meta">18 lessons · 90 graded questions · beginner</p>
        </div>

        <div className="course-pass__perf" aria-hidden="true" />

        <ul className="course-pass__list">
          {PASS_ROWS.map((row) => (
            <li key={row}>
              <Icon name="check" />
              <span>{row}</span>
            </li>
          ))}
        </ul>

        <p className="course-pass__foot">
          Python Programming works the same way: 20 lessons, ₹349 once, permanent access.
        </p>
      </article>

      <dl className="auth-stats">
        {STATS.map((stat) => (
          <div className="auth-stats__item" key={stat.label}>
            <dt className="auth-stats__value">{stat.value}</dt>
            <dd className="auth-stats__label">{stat.label}</dd>
          </div>
        ))}
      </dl>

      <div className="auth-story__loop">
        <span className="auth-story__step">
          <Icon name="play" /> Watch
        </span>
        <span className="auth-story__step-divider" aria-hidden="true" />
        <span className="auth-story__step">
          <Icon name="check" /> Reflect
        </span>
        <span className="auth-story__step-divider" aria-hidden="true" />
        <span className="auth-story__step is-gold">
          <Icon name="award" /> Prove
        </span>
      </div>

      <p className="auth-story__brand">
        Learnora
        <span>Rewards are funded by subscriptions and course passes, never a return on investment.</span>
      </p>
    </section>
  )
}

export default AuthStory
