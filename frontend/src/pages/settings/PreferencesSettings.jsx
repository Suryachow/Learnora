import { useCallback, useState } from 'react'

import { fetchPreferences, updatePreferences } from '../../api/account'
import Alert from '../../components/Alert'
import Switch from '../../components/Switch'
import { Loading } from '../../components/Spinner'
import useFetch from '../../hooks/useFetch'

const OPTIONS = [
  {
    key: 'notify_rewards',
    label: 'Reward confirmations',
    hint: 'Email me when a reward is added to my wallet.',
  },
  {
    key: 'notify_product_updates',
    label: 'Product updates',
    hint: 'Occasional news about new courses and features.',
  },
  {
    key: 'weekly_digest',
    label: 'Weekly digest',
    hint: 'A short summary of your progress every Monday.',
  },
]

/** Notification preferences. Each switch saves on its own, so nothing is lost. */
export function PreferencesSettings() {
  const load = useCallback(() => fetchPreferences(), [])
  const { data: preferences, loading, error, reload, setData } = useFetch(load)
  const [saving, setSaving] = useState('')
  const [notice, setNotice] = useState('')
  const [problem, setProblem] = useState('')

  if (loading) return <Loading label="Loading your preferences…" />

  if (error) {
    return (
      <section className="card">
        <h2 className="card__title">Notifications</h2>
        <Alert>{error.message}</Alert>
        <div className="form-actions">
          <button type="button" className="btn btn--secondary" onClick={reload}>
            Try again
          </button>
        </div>
      </section>
    )
  }

  async function toggle(key, value) {
    setProblem('')
    setNotice('')
    setSaving(key)
    try {
      const updated = await updatePreferences({ [key]: value })
      setData(updated)
      setNotice('Preferences saved.')
    } catch (err) {
      setProblem(err.message)
    } finally {
      setSaving('')
    }
  }

  return (
    <section className="card">
      <h2 className="card__title">Notifications</h2>
      <p className="card__subtitle">
        These control the emails we send you. They never affect your rewards or subscription.
      </p>

      <Alert>{problem}</Alert>
      <Alert tone="success">{notice}</Alert>

      <div className="stack">
        {OPTIONS.map((option) => (
          <Switch
            key={option.key}
            id={`pref-${option.key}`}
            checked={Boolean(preferences?.[option.key])}
            onChange={(value) => toggle(option.key, value)}
            label={option.label}
            hint={option.hint}
            disabled={saving === option.key}
          />
        ))}
      </div>

      <div className="row">
        <button type="button" className="btn btn--secondary" onClick={reload}>
          Reload from server
        </button>
      </div>
    </section>
  )
}

export default PreferencesSettings
