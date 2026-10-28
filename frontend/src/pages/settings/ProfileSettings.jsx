import { useState } from 'react'
import { Link } from 'react-router-dom'

import { updateMe } from '../../api/auth'
import Alert from '../../components/Alert'
import Button from '../../components/Button'
import FormField from '../../components/FormField'
import { useAuth } from '../../hooks/useAuth'
import { formatDate } from '../../utils/datetime'

/** Account details a learner can change themselves. */
export function ProfileSettings() {
  const { user, refresh } = useAuth()
  const [name, setName] = useState(user.name)
  const [saving, setSaving] = useState(false)
  const [notice, setNotice] = useState('')
  const [problem, setProblem] = useState('')

  if (!user) return null

  async function handleSubmit(event) {
    event.preventDefault()
    setProblem('')
    setNotice('')

    const cleaned = name.trim()
    if (cleaned.length < 2) {
      setProblem('Please enter your full name (at least 2 characters).')
      return
    }

    setSaving(true)
    try {
      await updateMe({ name: cleaned })
      await refresh()
      setNotice('Saved. Your new name is now shown across Learnora.')
    } catch (err) {
      setProblem(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <section className="card">
        <h2 className="card__title">Your details</h2>
        <form className="stack" onSubmit={handleSubmit}>
          <Alert>{problem}</Alert>
          <Alert tone="success">{notice}</Alert>

          <FormField
            id="profile-name"
            label="Display name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            autoComplete="name"
            hint="This is the name shown on your dashboard and welcome messages."
          />

          <FormField
            id="profile-email"
            label="Email address"
            type="email"
            value={user.email}
            onChange={() => {}}
            autoComplete="email"
            readOnly
            required={false}
            hint="Contact support if you need to change the email on your account."
          />

          <div className="form-actions">
            <Button type="submit" disabled={saving || name.trim() === user.name}>
              {saving ? 'Saving…' : 'Save changes'}
            </Button>
          </div>
        </form>
      </section>

      <section className="card">
        <h2 className="card__title">Account summary</h2>
        <dl className="definition-list">
          <dt>Member since</dt>
          <dd>{formatDate(user.created_at)}</dd>
          <dt>Role</dt>
          <dd>{user.is_admin ? 'Administrator' : 'Learner'}</dd>
          <dt>Subscription</dt>
          <dd>
            {user.has_active_subscription
              ? `Active until ${formatDate(user.subscribed_until)}`
              : 'Not subscribed'}
          </dd>
        </dl>

        <div className="row">
          <Link className="btn btn--secondary" to="/subscription">
            {user.has_active_subscription ? 'Manage subscription' : 'Subscribe'}
          </Link>
          <Link className="btn btn--secondary" to="/wallet">
            Open wallet
          </Link>
        </div>
      </section>
    </>
  )
}

export default ProfileSettings
