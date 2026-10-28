import { useCallback, useState } from 'react'
import { Link } from 'react-router-dom'

import * as subscriptionApi from '../api/subscription'
import Amount from '../components/Amount'
import Alert from '../components/Alert'
import Button from '../components/Button'
import { Loading } from '../components/Spinner'
import useFetch from '../hooks/useFetch'
import { useAuth } from '../hooks/useAuth'
import { formatDate } from '../utils/datetime'

/**
 * Buying the subscription.
 *
 * The browser can start a payment, but it can never mark one as paid. Only a
 * signature-verified provider webhook activates the plan, which is why the
 * screen waits for the server to confirm instead of trusting the redirect.
 */
export function SubscriptionPage() {
  const { user, refresh } = useAuth()

  const loadPlan = useCallback(() => subscriptionApi.fetchPlan(), [])
  const { data: plan, loading, error } = useFetch(loadPlan)

  const [order, setOrder] = useState(null)
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const [justSubscribed, setJustSubscribed] = useState(false)

  async function startCheckout() {
    setProblem('')
    setJustSubscribed(false)
    setBusy(true)
    try {
      setOrder(await subscriptionApi.createCheckout())
    } catch (err) {
      setProblem(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function confirmTestPayment() {
    setProblem('')
    setBusy(true)
    try {
      await subscriptionApi.simulatePayment(order.order_id)
      await refresh()
      setOrder(null)
      setJustSubscribed(true)
    } catch (err) {
      setProblem(err.message)
    } finally {
      setBusy(false)
    }
  }

  const subscribed = Boolean(user?.has_active_subscription)
  const usesMockGateway = order?.provider === 'mock' && order?.mock_payment_url

  return (
    <div className="stack">
      <header className="page-header">
        <h1>Subscription</h1>
        <p>
          Learning material is always free. A subscription is what unlocks the assessments that pay
          rewards.
        </p>
      </header>

      <Alert>{problem}</Alert>

      {justSubscribed ? (
        <Alert tone="success">
          Payment confirmed by the server. Your subscription is active — head to{' '}
          <Link to="/courses">Courses</Link> and start a task.
        </Alert>
      ) : null}

      {loading ? <Loading label="Loading the plan…" /> : null}
      <Alert>{error?.message}</Alert>

      {plan ? (
        <div className="sub-layout">
          <div className="sub-main">
            <section className="card card--highlight sub-plan">
              <p className="pill">{subscribed ? 'Active plan' : 'The plan'}</p>
              <h2 className="card__title">{plan.name}</h2>

              <div className="sub-plan__price">
                <Amount paise={plan.price_paise} className="amount-chip--plain" />
                <span className="price__period">for {plan.days} days</span>
              </div>

              <p>{plan.description}</p>

              <ul className="prose__list">
                <li>Every eligible task unlocked, across all courses.</li>
                <li>Rewards recorded in your wallet as soon as you pass.</li>
                <li>Full ledger of everything you have earned.</li>
                <li>Extending early never wastes the days you have already paid for.</li>
              </ul>

              {plan.rewards_enabled ? null : (
                <Alert tone="info">
                  Rewards are paused platform-wide right now. You can still subscribe and learn, but
                  new rewards will not be recorded until they are switched back on.
                </Alert>
              )}

              <div className="form-actions">
                <Button block onClick={startCheckout} disabled={busy}>
                  {busy
                    ? 'Contacting the payment provider…'
                    : subscribed
                      ? 'Extend subscription'
                      : 'Subscribe now'}
                </Button>
              </div>

              <div className="sub-facts">
                <div>
                  <span>Length</span>
                  <strong>{plan.days} days</strong>
                </div>
                <div>
                  <span>Currency</span>
                  <strong>{plan.currency}</strong>
                </div>
                <div>
                  <span>Processed by</span>
                  <strong>{plan.provider === 'mock' ? 'Test gateway' : 'Payment provider'}</strong>
                </div>
              </div>
            </section>

            {order ? (
              <section className="card">
                <h2 className="card__title">Payment in progress</h2>
                <dl className="definition-list">
                  <dt>Order</dt>
                  <dd>{order.order_id}</dd>
                  <dt>Amount</dt>
                  <dd>
                    <Amount paise={order.amount_paise} className="amount-chip--plain" />
                  </dd>
                </dl>

                {usesMockGateway ? (
                  <>
                    <Alert tone="info">
                      This server is using the built-in test gateway, so no real money moves. It still
                      sends a signed webhook through the same verification code the live gateway uses.
                    </Alert>
                    <div className="form-actions">
                      <Button onClick={confirmTestPayment} disabled={busy}>
                        {busy ? 'Confirming…' : 'Confirm the test payment'}
                      </Button>
                    </div>
                  </>
                ) : (
                  <Alert tone="info">
                    Complete the payment in the provider&apos;s window. If it did not open, restart
                    the checkout. Your plan activates as soon as the provider confirms the payment.
                  </Alert>
                )}

                <Button variant="ghost" onClick={() => setOrder(null)} disabled={busy}>
                  Cancel this payment
                </Button>
              </section>
            ) : null}
          </div>

          <aside className="sub-side">
            <section className="card">
              <h2 className="card__title">Your subscription</h2>
              {subscribed ? (
                <>
                  <p>
                    Active until <strong>{formatDate(user.subscribed_until)}</strong>.
                  </p>
                  <p className="card__subtitle">
                    Extending adds {plan.days} more days from the end of your current period, so you
                    never lose time you have already paid for.
                  </p>
                </>
              ) : (
                <p className="card__subtitle">
                  Not subscribed yet. You can read every course, topic and video before you decide.
                </p>
              )}
            </section>

            <section className="card">
              <h2 className="card__title">How activation works</h2>
              <ul className="prose__list">
                <li>Your browser starts the payment and nothing more.</li>
                <li>The payment provider sends a signed webhook to the SkillEarn server.</li>
                <li>The server verifies the signature, then records the payment and the active period.</li>
                <li>Repeat notifications are ignored, so you are never charged twice for one order.</li>
              </ul>
            </section>

            <section className="card">
              <h2 className="card__title">Where the money goes</h2>
              <p className="card__subtitle">
                Subscription money is revenue to Learnora. It is not the same as profit — rewards,
                processing fees, hosting and taxes all come out of it. See the{' '}
                <Link to="/rewards-policy">Rewards Policy</Link>.
              </p>
            </section>
          </aside>
        </div>
      ) : null}
    </div>
  )
}

export default SubscriptionPage
