"""Courses: the top level of the catalogue."""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Enum, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, CreatedAtMixin

if TYPE_CHECKING:
    from .purchase import CoursePurchase
    from .topic import Topic


class CourseLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class Course(Base, CreatedAtMixin):
    __tablename__ = "courses"
    __table_args__ = (
        CheckConstraint("price_paise >= 0", name="ck_courses_price_non_negative"),
        CheckConstraint(
            "duration_minutes IS NULL OR duration_minutes >= 0",
            name="ck_courses_duration_non_negative",
        ),
        CheckConstraint(
            "access_days IS NULL OR access_days >= 1", name="ck_courses_access_days_positive"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    #: What one learner pays from their wallet to unlock this course. 0 = free.
    price_paise: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    cover_image_url: Mapped[str | None] = mapped_column(String(500), default=None)
    level: Mapped[CourseLevel] = mapped_column(
        Enum(CourseLevel, native_enum=False, length=16, validate_strings=True),
        default=CourseLevel.beginner,
        server_default=CourseLevel.beginner.value,
        nullable=False,
    )
    #: Estimated study time for the whole course, in minutes.
    duration_minutes: Mapped[int | None] = mapped_column(Integer, default=None)
    #: "What you will learn": one short line per outcome.
    outcomes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    #: Days of access one purchase buys. NULL means the purchase never expires.
    access_days: Mapped[int | None] = mapped_column(Integer, default=None)

    topics: Mapped[list["Topic"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Topic.position",
    )
    purchases: Mapped[list["CoursePurchase"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Course id={self.id} title={self.title!r}>"
