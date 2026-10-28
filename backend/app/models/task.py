"""Assessments: quizzes (shipped) and coding tasks (deferred, see CodingTaskRunner)."""

import enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, CheckConstraint, Enum, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, CreatedAtMixin

if TYPE_CHECKING:
    from .attempt import Attempt
    from .topic import Topic


class TaskType(str, enum.Enum):
    quiz = "quiz"
    coding = "coding"


class Task(Base, CreatedAtMixin):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("pass_percent BETWEEN 0 AND 100", name="ck_tasks_pass_percent_range"),
        CheckConstraint("reward >= 0", name="ck_tasks_reward_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[TaskType] = mapped_column(
        Enum(TaskType, native_enum=False, length=16, validate_strings=True),
        default=TaskType.quiz,
        nullable=False,
    )
    pass_percent: Mapped[int] = mapped_column(Integer, default=70, nullable=False)
    reward: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Quiz: {"questions": [{"id", "prompt", "options": [...], "correct_index", "points"?}]}
    # Coding: {"spec": ..., "test_cases": [...]} - never sent to the client.
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    topic: Mapped["Topic"] = relationship(back_populates="tasks")
    attempts: Mapped[list["Attempt"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Task id={self.id} type={self.type.value} reward={self.reward}>"
