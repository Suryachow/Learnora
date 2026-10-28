const STEPS = [
  { id: 'account', index: 1, label: 'Account' },
  { id: 'pass', index: 2, label: 'Course pass' },
  { id: 'learn', index: 3, label: 'Unlock' },
]

/**
 * The three things that happen between signing up and opening an assessment.
 * Signing in lands on step one again, because the account is the only step the
 * form on this page covers.
 */
export function AuthSteps({ current = 'account' }) {
  const active = STEPS.findIndex((step) => step.id === current)

  return (
    <ol className="auth-steps" aria-label="From account to unlocked course">
      {STEPS.map((step, position) => {
        const state = position < active ? 'is-done' : position === active ? 'is-current' : ''
        const now = position === active ? 'step' : undefined

        return (
          <li className={`auth-steps__item ${state}`.trim()} key={step.id} aria-current={now}>
            <span className="auth-steps__index" aria-hidden="true">
              {position < active ? '✓' : step.index}
            </span>
            <span className="auth-steps__label">{step.label}</span>
            {position < STEPS.length - 1 ? (
              <span className="auth-steps__bar" aria-hidden="true" />
            ) : null}
          </li>
        )
      })}
    </ol>
  )
}

export default AuthSteps
