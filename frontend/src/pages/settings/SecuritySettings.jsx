import { useState } from 'react'

import { changePassword } from '../../api/account'
import Alert from '../../components/Alert'
import Button from '../../components/Button'
import FormField from '../../components/FormField'
import { useAuth } from '../../hooks/useAuth'

const EMPTY = { current: '', next: '', confirm: '' }

/** Change the password used to sign in, and end the session on this device. */
export function SecuritySettings() {
  const { signOut } = useAuth()
  const [fields, setFields] = useState(EMPTY)
  const [saving, setSaving] = useState(false)
  const [notice, setNotice] = useState('')
  const [problem, setProblem] = useState('')

  function change(key) {
    return (event) => setFields((current) => ({ ...current, [key]: event.target.value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setProblem('')
    setNotice('')

    if (fields.next.length < 8 || !/[a-zA-Z]/.test(fields.next) || !/\d/.test(fields.next)) {
      setProblem('Your new password needs at least 8 characters, including a letter and a number.')
      return
    }
    if (fields.next !== fields.confirm) {
      setProblem('The two new passwords do not match.')
      return
    }

    setSaving(true)
    try {
      await changePassword({ current_password: fields.current, new_password: fields.next })
      setFields(EMPTY)
      setNotice('Password changed. Use the new one the next time you sign in.')
    } catch (err) {
      setProblem(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <section className="card">
        <h2 className="card__title">Password</h2>
        <p className="card__subtitle">
          Choose a password you do not use anywhere else. It is hashed on the server and never
          stored in plain text.
        </p>

        <form className="stack" onSubmit={handleSubmit}>
          <Alert>{problem}</Alert>
          <Alert tone="success">{notice}</Alert>

          <FormField
            id="current-password"
            label="Current password"
            type="password"
            value={fields.current}
            onChange={change('current')}
            autoComplete="current-password"
          />

          <FormField
            id="new-password"
            label="New password"
            type="password"
            value={fields.next}
            onChange={change('next')}
            autoComplete="new-password"
            hint="At least 8 characters, with a letter and a number."
          />

          <FormField
            id="confirm-password"
            label="Confirm new password"
            type="password"
            value={fields.confirm}
            onChange={change('confirm')}
            autoComplete="new-password"
          />

          <div className="form-actions">
            <Button
              type="submit"
              disabled={saving || !fields.current || !fields.next || !fields.confirm}
            >
              {saving ? 'Changing…' : 'Change password'}
            </Button>
          </div>
        </form>
      </section>

      <section className="card">
        <h2 className="card__title">This device</h2>
        <p className="card__subtitle">
          Signing out removes the access token from this browser. You can sign back in at any time.
        </p>
        <div className="form-actions">
          <Button type="button" variant="secondary" onClick={signOut}>
            Sign out of this device
          </Button>
        </div>
      </section>
    </>
  )
}

export default SecuritySettings
