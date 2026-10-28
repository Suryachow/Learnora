"""Runtime application settings, editable from the admin console.

Secrets and infrastructure (JWT secret, database URL, payment keys) stay in
`.env` and are never exposed here. The *business* knobs live in this table so
an administrator can change them without a redeploy.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from ..utils import utcnow
from .base import Base


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[Any] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )
    # The administrator who last changed the value (nullable: seed/CLI writes).
    updated_by: Mapped[int | None] = mapped_column(Integer, default=None)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<AppSetting {self.key}={self.value!r}>"
