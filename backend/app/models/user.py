"""Accounts."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from ..utils import utcnow
from .base import Base, CreatedAtMixin


class User(Base, CreatedAtMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    subscribed_until: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    #: Notification/style choices. A JSON blob so new keys need no migration.
    preferences: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    @property
    def has_active_subscription(self) -> bool:
        return self.subscribed_until is not None and self.subscribed_until > utcnow()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<User id={self.id} email={self.email!r}>"
