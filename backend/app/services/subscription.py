"""Subscriptions: plan, checkout, and the only path that may activate a plan."""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Transaction, TransactionKind, TransactionStatus, User
from ..utils import utcnow
from .ledger import add_transaction
from .payments import PaymentEvent
from .settings_store import runtime_settings


class SubscriptionError(Exception):
    """Raised when a payment cannot be turned into a subscription."""


def plan_details(db: Session) -> dict:
    """The plan as advertised to the browser, using the *live* runtime settings."""
    live = runtime_settings(db)
    return {
        "name": "Learnora Subscription",
        "description": (
            f"Unlocks every eligible task for {live.subscription_days} days. "
            "Pass an assessment and the reward listed for that task is added to your wallet."
        ),
        "price_paise": live.subscription_price_paise,
        "days": live.subscription_days,
        "currency": "INR",
        "provider": settings.payment_provider,
        "rewards_enabled": live.rewards_enabled,
    }


def activate_subscription(
    db: Session,
    *,
    user_id: int,
    days: int,
    amount_paise: int,
    provider_ref: str,
    note: str = "",
) -> bool:
    """Extend a subscription and write the revenue row.

    Idempotent twice over: a fast check, and - the real guarantee - the unique
    constraint on `transactions.provider_ref`, which makes a duplicate webhook
    a no-op even if two requests arrive at the same moment.

    Returns True only when this call performed the activation.
    """
    already_recorded = db.scalar(
        select(Transaction.id).where(Transaction.provider_ref == provider_ref)
    )
    if already_recorded is not None:
        return False

    user = db.get(User, user_id)
    if user is None:
        raise SubscriptionError("That payment does not belong to a Learnora account.")

    # Extending early does not throw away time the user has already paid for.
    now = utcnow()
    start = user.subscribed_until if user.subscribed_until and user.subscribed_until > now else now
    user.subscribed_until = start + timedelta(days=days)

    add_transaction(
        db,
        user_id=user_id,
        kind=TransactionKind.subscription,
        amount=amount_paise,
        status=TransactionStatus.completed,
        note=note or f"{days}-day subscription",
        provider_ref=provider_ref,
    )

    try:
        db.commit()
    except IntegrityError:
        # A concurrent webhook for the same payment won the race. Let it stand.
        db.rollback()
        return False
    return True


def handle_payment_event(db: Session, event: PaymentEvent) -> bool:
    """Turn a *verified* payment outcome into a subscription."""
    if not event.paid:
        return False
    live = runtime_settings(db)
    return activate_subscription(
        db,
        user_id=event.user_id,
        days=live.subscription_days,
        amount_paise=event.amount_paise or live.subscription_price_paise,
        provider_ref=event.order_id,
        note=event.note,
    )
