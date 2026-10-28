"""The append-only ledger, and every balance derived from it.

Money rules:
  * amounts are signed integer paise
  * the wallet balance is computed here and is never stored
  * subscription and course payments are recorded for revenue reporting;
    a subscription is paid *to* Learnora and does not touch the wallet, a course
    bought through the gateway is paid to Learnora as well, while a course bought
    from the reward balance is paid *out* of the wallet and therefore debits it
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Transaction, TransactionKind, TransactionStatus
from ..utils import utcnow

#: Transaction kinds that move the user's wallet balance.
WALLET_KINDS = (
    TransactionKind.reward,
    TransactionKind.withdrawal,
    TransactionKind.course_purchase,
)

#: Every way a learner can buy a course. Both are negative rows - money leaving
#: the learner - so revenue reports them as an absolute figure.
COURSE_SALE_KINDS = (
    TransactionKind.course_purchase,
    TransactionKind.course_payment,
)


def add_transaction(
    db: Session,
    *,
    user_id: int,
    kind: TransactionKind,
    amount: int,
    status: TransactionStatus = TransactionStatus.completed,
    note: str = "",
    task_id: int | None = None,
    topic_id: int | None = None,
    course_id: int | None = None,
    provider_ref: str | None = None,
) -> Transaction:
    """Append one row. Callers commit (usually as part of a bigger transaction)."""
    transaction = Transaction(
        user_id=user_id,
        kind=kind,
        amount=amount,
        status=status,
        note=note[:255],
        task_id=task_id,
        topic_id=topic_id,
        course_id=course_id,
        provider_ref=provider_ref,
    )
    db.add(transaction)
    return transaction


def _sum_amount(
    db: Session,
    user_id: int,
    *,
    kinds: tuple[TransactionKind, ...],
    statuses: tuple[TransactionStatus, ...] | None = None,
    positive_only: bool = False,
    negative_only: bool = False,
) -> int:
    statement = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id, Transaction.kind.in_(kinds)
    )
    if statuses is not None:
        statement = statement.where(Transaction.status.in_(statuses))
    if positive_only:
        statement = statement.where(Transaction.amount > 0)
    if negative_only:
        statement = statement.where(Transaction.amount < 0)
    return int(db.scalar(statement) or 0)


def wallet_balance(db: Session, user_id: int) -> int:
    """Rewards earned minus withdrawals, counting only completed rows."""
    return _sum_amount(
        db,
        user_id,
        kinds=WALLET_KINDS,
        statuses=(TransactionStatus.completed,),
    )


def pending_balance(db: Session, user_id: int) -> int:
    """Rewards recorded but not yet finalised (shown separately in the UI)."""
    return _sum_amount(
        db,
        user_id,
        kinds=(TransactionKind.reward,),
        statuses=(TransactionStatus.pending,),
        positive_only=True,
    )


def lifetime_earned(db: Session, user_id: int) -> int:
    return _sum_amount(
        db,
        user_id,
        kinds=(TransactionKind.reward,),
        statuses=(TransactionStatus.completed,),
        positive_only=True,
    )


def total_withdrawn(db: Session, user_id: int) -> int:
    """Withdrawals are stored as negative amounts; reported as a positive figure."""
    return abs(
        _sum_amount(
            db,
            user_id,
            kinds=(TransactionKind.withdrawal,),
            statuses=(TransactionStatus.completed,),
            negative_only=True,
        )
    )


def rewards_paid_today(db: Session, user_id: int) -> int:
    """Used by the daily reward limit. Counts pending and completed rewards."""
    start_of_day = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    statement = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id,
        Transaction.kind == TransactionKind.reward,
        Transaction.amount > 0,
        Transaction.created_at >= start_of_day,
    )
    return int(db.scalar(statement) or 0)


def subscription_revenue(db: Session) -> int:
    """Total subscription money received - the revenue side of the admin report."""
    statement = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.kind == TransactionKind.subscription,
        Transaction.status == TransactionStatus.completed,
    )
    return int(db.scalar(statement) or 0)


def course_revenue(db: Session) -> int:
    """Course money received, however it was paid.

    Purchases are negative rows, so report the total as positive.
    """
    statement = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.kind.in_(COURSE_SALE_KINDS),
        Transaction.status == TransactionStatus.completed,
    )
    return abs(int(db.scalar(statement) or 0))


def total_revenue(db: Session) -> int:
    """Everything learners paid Learnora: subscriptions plus one-off course purchases."""
    return subscription_revenue(db) + course_revenue(db)


def list_transactions(
    db: Session,
    user_id: int,
    *,
    limit: int = 20,
    offset: int = 0,
    kind: TransactionKind | None = None,
) -> tuple[list[Transaction], int]:
    filters = [Transaction.user_id == user_id]
    if kind is not None:
        filters.append(Transaction.kind == kind)

    items = list(
        db.scalars(
            select(Transaction)
            .where(*filters)
            .order_by(Transaction.created_at.desc(), Transaction.id.desc())
            .limit(limit)
            .offset(offset)
        )
    )
    total = int(db.scalar(select(func.count(Transaction.id)).where(*filters)) or 0)
    return items, total
