"""Append-only money ledger.

The wallet balance is always *computed* from this table - never stored as a
mutable number - so it can be rebuilt and audited at any time.

Amounts are signed integer paise: credits are positive, debits are negative.
"""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, CreatedAtMixin

if TYPE_CHECKING:
    from .user import User


class TransactionKind(str, enum.Enum):
    subscription = "subscription"
    reward = "reward"
    withdrawal = "withdrawal"
    #: Money paid *out* of the wallet to unlock one course (a negative amount).
    course_purchase = "course_purchase"
    #: Money paid to Learnora through the payment gateway for one course. It never
    #: touches the wallet - the gateway took the money, not the reward balance.
    course_payment = "course_payment"


class TransactionStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


class Transaction(Base, CreatedAtMixin):
    __tablename__ = "transactions"
    __table_args__ = (
        # A reward can be recorded at most once per (user, task). NULL task_id
        # rows (subscriptions/withdrawals) are exempt, since most databases allow
        # repeated NULLs inside a unique constraint. This is the real guard
        # against double rewards - application checks alone are not enough.
        UniqueConstraint("user_id", "task_id", "kind", name="uq_transactions_user_task_kind"),
        # A video-completion reward can be recorded at most once per (user, topic).
        # Task rewards leave topic_id NULL, and NULLs never collide in a unique
        # constraint, so this only guards rows that name a topic.
        UniqueConstraint("user_id", "topic_id", "kind", name="uq_transactions_user_topic_kind"),
        # Makes webhook/order processing idempotent.
        UniqueConstraint("provider_ref", name="uq_transactions_provider_ref"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    kind: Mapped[TransactionKind] = mapped_column(
        Enum(TransactionKind, native_enum=False, length=16, validate_strings=True), nullable=False
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus, native_enum=False, length=16, validate_strings=True),
        default=TransactionStatus.completed,
        nullable=False,
    )
    note: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    task_id: Mapped[int | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"), default=None
    )
    #: Set only for a lesson reward, which is paid for a topic rather than a task.
    topic_id: Mapped[int | None] = mapped_column(
        ForeignKey("topics.id", ondelete="SET NULL"), default=None
    )
    #: Set only for a course purchase, so the ledger names what was bought.
    course_id: Mapped[int | None] = mapped_column(
        ForeignKey("courses.id", ondelete="SET NULL"), default=None
    )
    provider_ref: Mapped[str | None] = mapped_column(String(255), default=None)

    user: Mapped["User"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Transaction id={self.id} kind={self.kind.value} amount={self.amount}>"
