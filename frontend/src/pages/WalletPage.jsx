import { useCallback } from 'react'
import { Link } from 'react-router-dom'

import { fetchWallet } from '../api/wallet'
import Alert from '../components/Alert'
import Button from '../components/Button'
import EmptyState from '../components/EmptyState'
import { Icon } from '../components/Icon'
import { Loading } from '../components/Spinner'
import TransactionList from '../components/TransactionList'
import useFetch from '../hooks/useFetch'
import { useAuth } from '../hooks/useAuth'
import { formatPaise } from '../utils/money'

/** Balance, pending rewards and recent activity. */
export function WalletPage() {
  const { user } = useAuth()

  const loadWallet = useCallback(() => fetchWallet({ limit: 5 }), [])
  const { data: wallet, loading, error, reload } = useFetch(loadWallet)

  if (loading) return <Loading label="Loading your wallet…" />

  if (error) {
    return (
      <div className="stack">
        <Alert>{error.message}</Alert>
        <Button variant="secondary" onClick={reload}>
          Try loading your wallet again
        </Button>
      </div>
    )
  }

  if (!wallet) return null

  const transactions = wallet.transactions.items

  return (
    <div className="stack">
      <header className="page-header">
        <h1>Wallet and earnings</h1>
        <p>Every amount here comes from the ledger. Nothing is stored as a running total.</p>
      </header>

      {!wallet.rewards_enabled ? (
        <Alert tone="info">
          Rewards are paused platform-wide at the moment. Your existing balance is unaffected, but no
          new rewards will be recorded until they are switched back on.
        </Alert>
      ) : null}

      <section className="wallet-hero">
        <div className="wallet-hero__main">
          <p className="wallet-hero__label">Available balance</p>
          <p className="wallet-hero__value amount">{formatPaise(wallet.balance_paise)}</p>
          <p className="wallet-hero__hint">
            Rewards earned, minus withdrawals and the courses you have unlocked.
          </p>
        </div>

        <dl className="wallet-hero__stats">
          <div>
            <dt>Pending rewards</dt>
            <dd className="amount">{formatPaise(wallet.pending_paise)}</dd>
          </div>
          <div>
            <dt>Lifetime earned</dt>
            <dd className="amount">{formatPaise(wallet.lifetime_earned_paise)}</dd>
          </div>
          <div>
            <dt>Withdrawn</dt>
            <dd className="amount">{formatPaise(wallet.withdrawn_paise)}</dd>
          </div>
          <div>
            <dt>Ledger entries</dt>
            <dd className="amount">{wallet.transactions.total}</dd>
          </div>
        </dl>
      </section>

      {!user?.has_active_subscription ? (
        <Alert tone="info">
          Rewards only start once you have an active subscription.{' '}
          <Link to="/subscription">See the subscription</Link>.
        </Alert>
      ) : null}

      <div className="wallet-grid">
        <section className="section">
          <div className="section__header">
            <h2 className="section__title">Recent activity</h2>
            <Link to="/transactions">View all transactions</Link>
          </div>

          {transactions.length === 0 ? (
            <EmptyState title="Nothing in your wallet yet">
              Pass an assessment to earn your first reward. Start with{' '}
              <Link to="/courses">any course</Link> you like.
            </EmptyState>
          ) : (
            <TransactionList items={transactions} />
          )}
        </section>

        <aside className="wallet-side">
          <section className="card">
            <h2 className="card__title">Today&apos;s cap</h2>
            <p className="wallet-cap">
              <span className="amount">{formatPaise(wallet.daily_limit_paise)}</span>
              <span>per day across all tasks</span>
            </p>
            <p className="card__subtitle">
              {wallet.rewards_enabled ? (
                <span className="badge badge--success">Rewards are running</span>
              ) : (
                <span className="badge badge--warning">Rewards are paused</span>
              )}
            </p>
            <p className="card__subtitle">
              The cap resets daily and applies per account. It is enforced on the server when a
              reward is recorded, not in this screen.
            </p>
          </section>

          <section className="card">
            <h2 className="card__title">Withdrawals</h2>
            <p className="card__subtitle">
              Payouts are handled by a separate team, so there is no withdrawal button here yet.
              Your balance and the full ledger stay accurate and ready for that process.
            </p>
            <p className="card__subtitle">
              Read the <Link to="/rewards-policy">rewards policy</Link> for the payment schedule.
            </p>
          </section>

          <section className="card">
            <h2 className="card__title">Keep going</h2>
            <ul className="wallet-link-list">
              <li>
                <Link to="/courses">
                  <Icon name="book" />
                  Pick up a course
                </Link>
              </li>
              <li>
                <Link to="/transactions">
                  <Icon name="swap" />
                  Read the full ledger
                </Link>
              </li>
              <li>
                <Link to="/rewards-policy">
                  <Icon name="info" />
                  How rewards work
                </Link>
              </li>
            </ul>
          </section>
        </aside>
      </div>
    </div>
  )
}

export default WalletPage
