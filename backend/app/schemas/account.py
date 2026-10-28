"""Account self-service payloads: password, preferences and billing history."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _strength(cls, value: str) -> str:
        if not any(char.isalpha() for char in value):
            raise ValueError("Password must contain at least one letter.")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one number.")
        return value


class PreferencesOut(BaseModel):
    notify_rewards: bool
    notify_product_updates: bool
    weekly_digest: bool


class PreferencesUpdateRequest(BaseModel):
    """Only the keys present are changed."""

    notify_rewards: bool | None = None
    notify_product_updates: bool | None = None
    weekly_digest: bool | None = None

    def changes(self) -> dict[str, bool]:
        return self.model_dump(exclude_none=True)


class BillingEntryOut(BaseModel):
    id: int
    amount: int
    status: str
    note: str
    provider_ref: str | None
    created_at: datetime


class BillingOut(BaseModel):
    """The subscription side of the account: what is active, what was paid."""

    has_active_subscription: bool
    subscribed_until: datetime | None
    total_paid_paise: int
    payments: list[BillingEntryOut]
    total: int
