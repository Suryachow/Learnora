"""Subscription plan and checkout schemas."""

from datetime import datetime

from pydantic import BaseModel


class PlanOut(BaseModel):
    name: str
    description: str
    price_paise: int
    days: int
    currency: str
    provider: str
    rewards_enabled: bool


class CheckoutResponse(BaseModel):
    """What the browser needs in order to pay for the plan."""

    order_id: str
    amount_paise: int
    currency: str
    provider: str
    key_id: str | None = None
    # Only populated by the mock provider in development.
    mock_payment_url: str | None = None


class SubscriptionStatusOut(BaseModel):
    has_active_subscription: bool
    subscribed_until: datetime | None
