"""Topics: a single lesson inside a course, with markdown notes and a video."""

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, CreatedAtMixin

if TYPE_CHECKING:
    from .course import Course
    from .task import Task


class Topic(Base, CreatedAtMixin):
    __tablename__ = "topics"
    __table_args__ = (CheckConstraint("position >= 0", name="ck_topics_position_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    video_url: Mapped[str | None] = mapped_column(String(500), default=None)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    course: Mapped["Course"] = relationship(back_populates="topics")
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="topic",
        cascade="all, delete-orphan",
        order_by="Task.id",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Topic id={self.id} title={self.title!r}>"
