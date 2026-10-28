"""Every submission a user makes against a task."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, CreatedAtMixin

if TYPE_CHECKING:
    from .task import Task
    from .user import User


class Attempt(Base, CreatedAtMixin):
    __tablename__ = "attempts"
    __table_args__ = (
        CheckConstraint("percent BETWEEN 0 AND 100", name="ck_attempts_percent_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), index=True, nullable=False
    )
    percent: Mapped[int] = mapped_column(Integer, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship()
    task: Mapped["Task"] = relationship(back_populates="attempts")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Attempt user={self.user_id} task={self.task_id} percent={self.percent}>"
