import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import Alert from '../components/Alert'
import AuthSteps from '../components/AuthSteps'
import AuthStory from '../components/AuthStory'
import Button from '../components/Button'
import FormField from '../components/FormField'
import { Icon } from '../components/Icon'
import { useAuth } from '../hooks/useAuth'

export function LoginPage() {
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const redirectTo = location.state?.from?.pathname || null

  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  function update(field) {
    return (event) => setForm((current) => ({ ...current, [field]: event.target.value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const user = await signIn({ email: form.email.trim(), password: form.password })
      navigate(redirectTo || (user?.is_admin ? '/admin' : '/dashboard'), { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-split">
      <AuthStory mode="login" />

      <div className="auth-panel">
        <AuthSteps current="account" />

        <div className="card auth-card">
          <header className="auth-card__head">
            <p className="auth-card__eyebrow">Welcome back</p>
            <h1 className="auth-card__title">Sign in to Learnora</h1>
            <p className="auth-card__lead">
              Your lessons, check-ins and rewards are exactly where you left them.
            </p>
          </header>

          <form className="stack" onSubmit={handleSubmit} noValidate={false}>
            <Alert>{error}</Alert>

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
              autoComplete="current-password"
              placeholder="Your password"
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

            <Button type="submit" block disabled={submitting}>
              {submitting ? 'Signing in…' : 'Sign in'}
            </Button>
          </form>

          <ul className="auth-trust">
            <li>
              <Icon name="check" /> Progress, attempts and wallet are saved
            </li>
            <li>
              <Icon name="coins" /> A course pass opens every assessment in that course
            </li>
            <li>
              <Icon name="shield" /> Passwords are hashed, sessions are signed
            </li>
          </ul>
        </div>

        <p className="form-footer">
          New to Learnora? <Link to="/signup">Create an account</Link>
        </p>
        <p className="auth-fine">
          Rewards are funded by subscriptions and course passes.{' '}
          <Link to="/rewards-policy">Read the policy</Link>.
        </p>
      </div>
    </div>
  )
}

export default LoginPage
