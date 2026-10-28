import { useCallback, useState } from 'react'
import { Link } from 'react-router-dom'

import { fetchWallet } from '../api/wallet'
import Alert from '../components/Alert'
import Button from '../components/Button'
import EmptyState from '../components/EmptyState'
import { Loading } from '../components/Spinner'
import TransactionList from '../components/TransactionList'
import useFetch from '../hooks/useFetch'
import { formatPaise } from '../utils/money'

const PAGE_SIZE = 10

const KIND_FILTERS = [
  { label: 'Everything', value: '' },
  { label: 'Rewards', value: 'reward' },
  { label: 'Subscriptions', value: 'subscription' },
  { label: 'Course purchases', value: 'course_purchase' },
  { label: 'Course payments', value: 'course_payment' },
  { label: 'Withdrawals', value: 'withdrawal' },
]

/** The full, append-only ledger for one account. */
export function TransactionsPage() {
  const [kind, setKind] = useState('')
  const [offset, setOffset] = useState(0)

  const loadWallet = useCallback(
    () => fetchWallet({ limit: PAGE_SIZE, offset, kind: kind || undefined }),
    [offset, kind],
  )
  const { data: wallet, loading, error, reload } = useFetch(loadWallet)

  function changeFilter(value) {
    setKind(value)
    setOffset(0)
  }

  const page = wallet?.transactions
  const shown = page?.items.length ?? 0
  const hasPrevious = offset > 0
  const hasNext = page ? offset + shown < page.total : false

  return (
    <div className="stack">
      <header className="page-header">
        <h1>Transaction history</h1>
        <p>An append-only record: rows are added, never edited or deleted.</p>
      </header>

      {wallet ? (
        <div className="stat-grid" data-stagger>
          <div className="stat stat--money">
            <span className="stat__label">Available balance</span>
            <span className="stat__value amount">{formatPaise(wallet.balance_paise)}</span>
          </div>
          <div className="stat stat--money">
            <span className="stat__label">Lifetime earned</span>
            <span className="stat__value amount">{formatPaise(wallet.lifetime_earned_paise)}</span>
          </div>
          <div className="stat">
            <span className="stat__label">Entries recorded</span>
            <span className="stat__value">{wallet.transactions.total}</span>
          </div>
        </div>
      ) : null}

      <div className="chips" role="group" aria-label="Filter transactions by type">
        {KIND_FILTERS.map((filter) => (
          <button
            key={filter.value || 'all'}
            type="button"
            className="chip"
            aria-pressed={kind === filter.value}
            onClick={() => changeFilter(filter.value)}
          >
            {filter.label}
          </button>
        ))}
      </div>

      <Alert>{error?.message}</Alert>

      {loading ? <Loading label="Loading your transactions…" /> : null}

      {!loading && page && page.items.length === 0 ? (
        <EmptyState
          title={kind ? 'Nothing of that kind yet' : 'No transactions yet'}
          action={
            kind ? (
              <Button variant="secondary" onClick={() => changeFilter('')}>
                Show everything
              </Button>
            ) : (
              <Link className="btn btn--primary" to="/courses">
                Browse courses
              </Link>
            )
          }
        >
          {kind
            ? 'Try a different filter to see the rest of your history.'
            : 'Your subscription payments and rewards will be listed here.'}
        </EmptyState>
      ) : null}

      {!loading && page && page.items.length > 0 ? (
        <>
          <TransactionList items={page.items} />
          <div className="pagination">
            <Button
              variant="secondary"
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
              disabled={!hasPrevious}
            >
              Newer
            </Button>
            <span className="muted">
              Showing {offset + 1}–{offset + shown} of {page.total}
            </span>
            <Button
              variant="secondary"
              onClick={() => setOffset(offset + PAGE_SIZE)}
              disabled={!hasNext}
            >
              Older
            </Button>
          </div>
        </>
      ) : null}

      {error ? (
        <Button variant="secondary" onClick={reload}>
          Try loading your history again
        </Button>
      ) : null}
    </div>
  )
}

export default TransactionsPage
