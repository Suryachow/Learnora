import { useCallback, useState } from 'react'
import { Link } from 'react-router-dom'

import { fetchSettings, resetSetting, updateSettings } from '../../api/admin'
import Alert from '../../components/Alert'
import Badge from '../../components/Badge'
import Button from '../../components/Button'
import Switch from '../../components/Switch'
import { Loading } from '../../components/Spinner'
import useFetch from '../../hooks/useFetch'
import { formatPaise } from '../../utils/money'

function grouped(settings) {
  const groups = new Map()
  for (const setting of settings) {
    if (!groups.has(setting.group)) groups.set(setting.group, [])
    groups.get(setting.group).push(setting)
  }
  return [...groups.entries()]
}

/** The business knobs an admin can change without a redeploy. */
export function AdminSettingsPage() {
  const load = useCallback(() => fetchSettings(), [])
  const { data: settings, loading, error, reload, setData } = useFetch(load)
  const [draft, setDraft] = useState({})
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const [notice, setNotice] = useState('')

  if (loading) return <Loading label="Loading settings…" />

  if (error) {
    return (
      <div className="stack">
        <Alert>{error.message}</Alert>
        <button type="button" className="btn btn--secondary" onClick={reload}>
          Try again
        </button>
      </div>
    )
  }

  const touched = Object.keys(draft)

  function valueOf(setting) {
    return touched.includes(setting.key) ? draft[setting.key] : setting.value
  }

  async function save() {
    setBusy(true)
    setProblem('')
    setNotice('')
    try {
      const values = {}
      for (const key of touched) {
        const setting = settings.find((row) => row.key === key)
        values[key] = setting.kind === 'bool' ? Boolean(draft[key]) : Number(draft[key])
      }
      setData(await updateSettings(values))
      setDraft({})
      setNotice('Settings saved. They apply to the next request.')
    } catch (err) {
      setProblem(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function reset(key) {
    setBusy(true)
    setProblem('')
    setNotice('')
    try {
      setData(await resetSetting(key))
      setDraft((current) => {
        const next = { ...current }
        delete next[key]
        return next
      })
      setNotice('Setting reset to the environment default.')
    } catch (err) {
      setProblem(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="stack">
      <header className="page-header">
        <h1>Settings</h1>
        <p>
          These values live in the database and take effect immediately. Secrets stay in the server
          environment.
        </p>
      </header>

      <Alert>{problem}</Alert>
      <Alert tone="success">{notice}</Alert>

      {grouped(settings).map(([group, rows]) => (
        <section className="card" key={group}>
          <h2 className="card__title">{group}</h2>

          <div className="stack">
            {rows.map((setting) => {
              const value = valueOf(setting)
              return (
                <div className="field" key={setting.key}>
                  {setting.kind === 'bool' ? (
                    <>
                      <Switch
                        id={`setting-${setting.key}`}
                        label={setting.label}
                        checked={Boolean(value)}
                        onChange={(checked) => setDraft({ ...draft, [setting.key]: checked })}
                        hint={setting.description}
                        disabled={busy}
                      />
                      <div className="row">
                        {setting.is_overridden ? (
                          <Badge tone="info">Overridden</Badge>
                        ) : (
                          <Badge tone="neutral">Using default</Badge>
                        )}
                        {setting.is_overridden ? (
                          <Button
                            variant="secondary"
                            disabled={busy}
                            onClick={() => reset(setting.key)}
                          >
                            Reset
                          </Button>
                        ) : null}
                      </div>
                    </>
                  ) : (
                    <>
                      <label className="field__label" htmlFor={`setting-${setting.key}`}>
                        {setting.label}
                        {setting.unit ? ` (${setting.unit})` : ''}
                      </label>
                      <input
                        id={`setting-${setting.key}`}
                        className="field__input"
                        type="number"
                        min={setting.minimum ?? undefined}
                        max={setting.maximum ?? undefined}
                        value={value}
                        disabled={busy}
                        onChange={(event) =>
                          setDraft({ ...draft, [setting.key]: event.target.value })
                        }
                      />
                      <span className="field__hint">{setting.description}</span>
                      <span className="field__hint">
                        Default {String(setting.default)}
                        {setting.unit === 'paise'
                          ? ` (${formatPaise(Number(setting.default))})`
                          : ''}
                        {setting.minimum != null || setting.maximum != null
                          ? ` · range ${setting.minimum ?? '—'} to ${setting.maximum ?? '—'}`
                          : ''}
                      </span>
                      {setting.is_overridden ? (
                        <div className="row">
                          <Badge tone="info">Overridden</Badge>
                          <Button
                            variant="secondary"
                            disabled={busy}
                            onClick={() => reset(setting.key)}
                          >
                            Reset to default
                          </Button>
                        </div>
                      ) : null}
                    </>
                  )}
                </div>
              )
            })}
          </div>
        </section>
      ))}

      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
        <span className="kpi__hint">
          {touched.length
            ? `${touched.length} unsaved change${touched.length === 1 ? '' : 's'}`
            : 'No unsaved changes.'}
        </span>
        <div className="row">
          <Button variant="secondary" disabled={busy || !touched.length} onClick={() => setDraft({})}>
            Discard
          </Button>
          <Button disabled={busy || !touched.length} onClick={save}>
            {busy ? 'Saving…' : 'Save settings'}
          </Button>
        </div>
      </div>

      <p className="card__subtitle">
        Reward payouts are governed by the <Link to="/rewards-policy">Rewards Policy</Link>; these
        switches never change a reward already recorded in the ledger.
      </p>
    </div>
  )
}

export default AdminSettingsPage
