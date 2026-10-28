"""User-facing representations of an account. Never expose `password_hash`."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    is_admin: bool
    has_active_subscription: bool
    subscribed_until: datetime | None
    created_at: datetime


class UserUpdateRequest(BaseModel):
    name: str | None = None
