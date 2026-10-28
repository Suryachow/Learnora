import { formatDateTime } from '../utils/datetime'
import { formatPaise, formatSignedPaise } from '../utils/money'

const KIND_LABELS = {
  subscription: 'Subscription',
  reward: 'Reward earned',
  withdrawal: 'Withdrawal',
  course_purchase: 'Course purchase',
  course_payment: 'Course payment',
}

const STATUS_LABELS = {
  pending: 'Pending',
  completed: 'Completed',
  failed: 'Failed',
}

/**
 * The ledger is append-only, so this list is the single source of truth for
 * what happened. Gold marks wallet money only - a subscription payment is
 * revenue to Learnora, not part of the learner's balance.
 */
export function TransactionList({ items }) {
  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th scope="col">When</th>
            <th scope="col">Type</th>
            <th scope="col">Details</th>
            <th scope="col" className="table__amount">
              Amount
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const isWalletMoney = item.kind !== 'subscription'
            return (
              <tr key={item.id}>
                <td className="table__nowrap">{formatDateTime(item.created_at)}</td>
                <td>
                  <span className="pill pill--soft">{KIND_LABELS[item.kind] ?? item.kind}</span>
                  {item.status !== 'completed' ? (
                    <span className="pill">{STATUS_LABELS[item.status] ?? item.status}</span>
                  ) : null}
                </td>
                <td>{item.note || '—'}</td>
                <td className="table__amount">
                  {isWalletMoney ? (
                    <span className="amount">{formatSignedPaise(item.amount)}</span>
                  ) : (
                    <span className="muted">{formatPaise(item.amount)}</span>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export default TransactionList
