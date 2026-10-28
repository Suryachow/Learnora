"""How far a user has got through one topic.

The video completion is recorded by the browser (a YouTube iframe cannot be
verified server-side), but the server only accepts it when the reported watch
time covers almost the whole runtime. Everything else on the row - the
understanding rating - is only accepted *after* that completion.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, CreatedAtMixin

if TYPE_CHECKING:
    from .topic import Topic
    from .user import User


class Understanding(str, enum.Enum):
    """The self-rating a learner gives straight after the video."""

    not_yet = "not_yet"
    mostly = "mostly"
    confident = "confident"


class TopicProgress(Base, CreatedAtMixin):
    __tablename__ = "topic_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "topic_id", name="uq_topic_progress_user_topic"),
        CheckConstraint(
            "video_watched_seconds >= 0 AND video_duration_seconds >= 0",
            name="ck_topic_progress_watch_times_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # Set once, when the video first reached its end.
    video_completed_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    video_watched_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    video_duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Set once, after the video was completed.
    understanding: Mapped[Understanding | None] = mapped_column(
        Enum(Understanding, native_enum=False, length=16, validate_strings=True),
        default=None,
    )
    understanding_note: Mapped[str] = mapped_column(Text, default="", nullable=False)
    understood_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    user: Mapped["User"] = relationship()
    topic: Mapped["Topic"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<TopicProgress user={self.user_id} topic={self.topic_id}>"
