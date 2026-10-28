import { useCallback, useState } from 'react'

import { fetchUsers, updateUser } from '../../api/admin'
import Amount from '../../components/Amount'
import Alert from '../../components/Alert'
import Badge from '../../components/Badge'
import Button from '../../components/Button'
import { Loading } from '../../components/Spinner'
import useFetch from '../../hooks/useFetch'
import { formatDate } from '../../utils/datetime'

const PAGE_SIZE = 25

/** Search accounts and change what they are allowed to do. */
export function AdminUsersPage() {
  const [search, setSearch] = useState('')
  const [query, setQuery] = useState('')
  const [offset, setOffset] = useState(0)
  const [busy, setBusy] = useState(null)
  const [problem, setProblem] = useState('')
  const [notice, setNotice] = useState('')

  const load = useCallback(
    () => fetchUsers({ search: query || undefined, limit: PAGE_SIZE, offset }),
    [query, offset],
  )
  const { data, loading, error, reload, setData } = useFetch(load)

  async function act(user, changes, message) {
    setBusy(user.id)
    setProblem('')
    setNotice('')
    try {
      const updated = await updateUser(user.id, changes)
      setData((current) =>
        current
          ? { ...current, items: current.items.map((row) => (row.id === user.id ? updated : row)) }
          : current,
      )
      setNotice(message)
    } catch (err) {
      setProblem(err.message)
    } finally {
      setBusy(null)
    }
  }

  const total = data?.total ?? 0

  return (
    <div className="stack">
      <header className="page-header">
        <h1>Users</h1>
        <p>Every account, what it holds, and the switches an admin controls.</p>
      </header>

      <div className="toolbar">
        <form
          className="toolbar__actions"
          onSubmit={(event) => {
            event.preventDefault()
            setOffset(0)
            setQuery(search.trim())
          }}
        >
          <input
            className="field__input"
            type="search"
            placeholder="Search by name or email"
            aria-label="Search users"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <Button type="submit" variant="secondary">
            Search
          </Button>
          {query ? (
            <Button
              variant="secondary"
              onClick={() => {
                setSearch('')
                setQuery('')
                setOffset(0)
              }}
            >
              Clear
            </Button>
          ) : null}
        </form>
      </div>

      <Alert>{problem}</Alert>
      <Alert tone="success">{notice}</Alert>

      {loading ? <Loading label="Loading accounts…" /> : null}

      {error ? (
        <div className="stack">
          <Alert>{error.message}</Alert>
          <button type="button" className="btn btn--secondary" onClick={reload}>
            Try again
          </button>
        </div>
      ) : null}

      {data ? (
        <section className="card">
          <h2 className="card__title">
            {total} account{total === 1 ? '' : 's'}
          </h2>

          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">Learner</th>
                  <th scope="col">Role</th>
                  <th scope="col">Subscription</th>
                  <th scope="col">Wallet</th>
                  <th scope="col">Learned</th>
                  <th scope="col">Attempts</th>
                  <th scope="col" />
                </tr>
              </thead>
              <tbody>
                {data.items.map((user) => (
                  <tr key={user.id}>
                    <td>
                      {user.name}
                      <br />
                      <span className="kpi__hint">{user.email}</span>
                      <br />
                      <span className="kpi__hint">Joined {formatDate(user.created_at)}</span>
                    </td>
                    <td>
                      <Badge tone={user.is_admin ? 'info' : 'neutral'}>
                        {user.is_admin ? 'Admin' : 'Learner'}
                      </Badge>
                    </td>
                    <td>
                      {user.has_active_subscription ? (
                        <>
                          <Badge tone="success">Active</Badge>
                          <br />
                          <span className="kpi__hint">until {formatDate(user.subscribed_until)}</span>
                        </>
                      ) : (
                        <Badge tone="neutral">None</Badge>
                      )}
                    </td>
                    <td>
                      <Amount paise={user.wallet_balance_paise} compact />
                    </td>
                    <td>
                      <Amount paise={user.lifetime_earned_paise} compact />
                    </td>
                    <td>
                      {user.attempt_count}
                      <br />
                      <span className="kpi__hint">{user.passed_count} passed</span>
                    </td>
                    <td>
                      <div className="table__actions">
                        {user.has_active_subscription ? (
                          <Button
                            variant="secondary"
                            disabled={busy === user.id}
                            onClick={() =>
                              act(
                                user,
                                { revoke_subscription: true },
                                `Subscription removed for ${user.email}.`,
                              )
                            }
                          >
                            Revoke sub
                          </Button>
                        ) : (
                          <Button
                            variant="secondary"
                            disabled={busy === user.id}
                            onClick={() =>
                              act(
                                user,
                                { grant_subscription_days: 30 },
                                `30 days granted to ${user.email}.`,
                              )
                            }
                          >
                            Grant 30 days
                          </Button>
                        )}

                        <Button
                          variant="secondary"
                          disabled={busy === user.id}
                          onClick={() =>
                            act(
                              user,
                              { is_admin: !user.is_admin },
                              user.is_admin
                                ? `${user.email} is no longer an admin.`
                                : `${user.email} is now an admin.`,
                            )
                          }
                        >
                          {user.is_admin ? 'Remove admin' : 'Make admin'}
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="kpi__hint">
              Showing {data.items.length} of {total}
            </span>
            <div className="row">
              <Button
                variant="secondary"
                disabled={offset === 0}
                onClick={() => setOffset((value) => Math.max(0, value - PAGE_SIZE))}
              >
                Previous
              </Button>
              <Button
                variant="secondary"
                disabled={offset + PAGE_SIZE >= total}
                onClick={() => setOffset((value) => value + PAGE_SIZE)}
              >
                Next
              </Button>
            </div>
          </div>
        </section>
      ) : null}
    </div>
  )
}

export default AdminUsersPage
