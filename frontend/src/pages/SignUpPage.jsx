import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import Alert from '../components/Alert'
import AuthSteps from '../components/AuthSteps'
import AuthStory from '../components/AuthStory'
import Button from '../components/Button'
import FormField from '../components/FormField'
import { Icon } from '../components/Icon'
import { useAuth } from '../hooks/useAuth'

/** The same three rules the server enforces, checked as the learner types. */
const PASSWORD_RULES = [
  { id: 'length', label: '8 characters or more', test: (value) => value.length >= 8 },
  { id: 'letter', label: 'One letter', test: (value) => /[a-z]/i.test(value) },
  { id: 'number', label: 'One number', test: (value) => /\d/.test(value) },
]

export function SignUpPage() {
  const { signUp } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  function update(field) {
    return (event) => setForm((current) => ({ ...current, [field]: event.target.value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')

    if (form.password.length < 8) {
      setError('Please choose a password with at least 8 characters.')
      return
    }

    setSubmitting(true)
    try {
      await signUp({
        name: form.name.trim(),
        email: form.email.trim(),
        password: form.password,
      })
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-split">
      <AuthStory mode="signup" />

      <div className="auth-panel">
        <AuthSteps current="account" />

        <div className="card auth-card">
          <header className="auth-card__head">
            <p className="auth-card__eyebrow">Free to join</p>
            <h1 className="auth-card__title">Create your account</h1>
            <p className="auth-card__lead">
              No card, no trial timer. Read every lesson first, then unlock a course for ₹349 when
              you want its assessments.
            </p>
          </header>

          <form className="stack" onSubmit={handleSubmit}>
            <Alert>{error}</Alert>

            <FormField
              id="name"
              label="Full name"
              value={form.name}
              onChange={update('name')}
              autoComplete="name"
              placeholder="Asha Rao"
            />

            <FormField
              id="email"
              label="Email address"
              type="email"
              value={form.email}
              onChange={update('email')}
              autoComplete="email"
              placeholder="you@example.com"
            />

            <FormField
              id="password"
              label="Password"
              type={showPassword ? 'text' : 'password'}
              value={form.password}
              onChange={update('password')}
              autoComplete="new-password"
              placeholder="At least 8 characters"
              aria-describedby="password-rules"
              trailing={
                <button
                  type="button"
                  className="field__toggle"
                  onClick={() => setShowPassword((current) => !current)}
                  aria-pressed={showPassword}
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              }
            />

            <ul className="pw-rules" id="password-rules">
              {PASSWORD_RULES.map((rule) => {
                const met = rule.test(form.password)
                return (
                  <li className={`pw-rule ${met ? 'is-met' : ''}`.trim()} key={rule.id}>
                    <span className="pw-rule__dot" aria-hidden="true" />
                    {rule.label}
                  </li>
                )
              })}
            </ul>

            <Button type="submit" block disabled={submitting}>
              {submitting ? 'Creating your account…' : 'Create account'}
            </Button>
          </form>

          <ul className="auth-trust">
            <li>
              <Icon name="book" /> Free to read: notes and video on every lesson
            </li>
            <li>
              <Icon name="lock" /> ₹349 per course, permanent access, no auto-renew
            </li>
            <li>
              <Icon name="coins" /> Every reward traces back to the attempt that paid it
            </li>
          </ul>
        </div>

        <p className="form-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
        <p className="auth-fine">
          By creating an account you agree to keep your check-ins honest.{' '}
          <Link to="/rewards-policy">Rewards policy</Link>.
        </p>
      </div>
    </div>
  )
}

export default SignUpPage
