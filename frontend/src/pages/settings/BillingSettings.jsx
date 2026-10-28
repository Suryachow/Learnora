import { useCallback } from 'react'
import { Link } from 'react-router-dom'

import { fetchBilling } from '../../api/account'
import Amount from '../../components/Amount'
import Alert from '../../components/Alert'
import Badge from '../../components/Badge'
import { Loading } from '../../components/Spinner'
import useFetch from '../../hooks/useFetch'
import { formatDateTime } from '../../utils/datetime'

const STATUS_TONES = { paid: 'success', pending: 'warning', failed: 'danger' }

/** What is active on the subscription and every payment made against it. */
export function BillingSettings() {
  const load = useCallback(() => fetchBilling({ limit: 20 }), [])
  const { data: billing, loading, error, reload } = useFetch(load)

  if (loading) return <Loading label="Loading your billing history…" />

  if (error) {
    return (
      <section className="card">
        <h2 className="card__title">Billing</h2>
        <Alert>{error.message}</Alert>
        <div className="form-actions">
          <button type="button" className="btn btn--secondary" onClick={reload}>
            Try again
          </button>
        </div>
      </section>
    )
  }

  return (
    <>
      <section className="card">
        <h2 className="card__title">Subscription</h2>
        <dl className="definition-list">
          <dt>Status</dt>
          <dd>
            <Badge tone={billing.has_active_subscription ? 'success' : 'neutral'}>
              {billing.has_active_subscription ? 'Active' : 'Not subscribed'}
            </Badge>
          </dd>
          {billing.has_active_subscription ? (
            <>
              <dt>Renews</dt>
              <dd>{formatDateTime(billing.subscribed_until)}</dd>
            </>
          ) : null}
          <dt>Total paid</dt>
          <dd>
            <Amount paise={billing.total_paid_paise} />
          </dd>
        </dl>

        <div className="row">
          <Link className="btn" to="/subscription">
            {billing.has_active_subscription ? 'Manage subscription' : 'Subscribe'}
          </Link>
          <Link className="btn btn--secondary" to="/rewards-policy">
            Rewards policy
          </Link>
        </div>
      </section>

      <section className="card">
        <h2 className="card__title">Payments</h2>
        <p className="card__subtitle">
          {billing.total === 0
            ? 'No payments yet.'
            : `${billing.total} payment${billing.total === 1 ? '' : 's'} recorded on your account.`}
        </p>

        {billing.payments.length ? (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">When</th>
                  <th scope="col">Amount</th>
                  <th scope="col">Status</th>
                  <th scope="col">Reference</th>
                </tr>
              </thead>
              <tbody>
                {billing.payments.map((payment) => (
                  <tr key={payment.id}>
                    <td>{formatDateTime(payment.created_at)}</td>
                    <td>
                      <Amount paise={payment.amount} compact />
                    </td>
                    <td>
                      <Badge tone={STATUS_TONES[payment.status] ?? 'neutral'}>
                        {payment.status}
                      </Badge>
                    </td>
                    <td>{payment.provider_ref ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </>
  )
}

export default BillingSettings
