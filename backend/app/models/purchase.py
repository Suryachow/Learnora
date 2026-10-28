"""Course purchases: what a learner unlocked with their wallet balance.

One row per (user, course) - the *current* entitlement. Every payment itself is
an append-only ledger row, so the audit trail lives in `transactions` and this
table only answers "may this learner open the course, and until when?".
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..utils import utcnow
from .base import Base

if TYPE_CHECKING:
    from .course import Course
    from .user import User


class CoursePurchase(Base):
    __tablename__ = "course_purchases"
    __table_args__ = (
        # One entitlement per learner and course: buying again extends it.
        UniqueConstraint("user_id", "course_id", name="uq_course_purchases_user_course"),
        CheckConstraint("amount_paise >= 0", name="ck_course_purchases_amount_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    #: What the learner actually paid for the most recent purchase.
    amount_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    purchased_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    #: NULL means permanent access, which is what a blank `access_days` buys.
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    user: Mapped["User"] = relationship()
    course: Mapped["Course"] = relationship(back_populates="purchases")

    @property
    def is_active(self) -> bool:
        return self.expires_at is None or self.expires_at > utcnow()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<CoursePurchase user_id={self.user_id} course_id={self.course_id}>"
