"""Account self-service: password changes, preferences and billing history."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Transaction, TransactionKind, TransactionStatus, User
from .security import hash_password, verify_password


class AccountError(Exception):
    """A request the signed-in user cannot make. `status_code` maps to HTTP."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


#: Preferences with their defaults. Adding a key here is all that is needed.
PREFERENCE_DEFAULTS: dict[str, bool] = {
    "notify_rewards": True,
    "notify_product_updates": True,
    "weekly_digest": False,
}


def read_preferences(user: User) -> dict[str, bool]:
    stored = user.preferences or {}
    return {
        key: bool(stored.get(key, default)) for key, default in PREFERENCE_DEFAULTS.items()
    }


def update_preferences(db: Session, user: User, changes: dict) -> dict[str, bool]:
    unknown = set(changes) - set(PREFERENCE_DEFAULTS)
    if unknown:
        raise AccountError(f"Unknown preference(s): {', '.join(sorted(unknown))}.")

    merged = read_preferences(user)
    for key, value in changes.items():
        merged[key] = bool(value)

    user.preferences = merged
    db.add(user)
    db.commit()
    db.refresh(user)
    return merged


def change_password(db: Session, user: User, *, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise AccountError("Your current password is not correct.", 400)
    if current_password == new_password:
        raise AccountError("Please choose a password you have not used here before.", 400)

    user.password_hash = hash_password(new_password)
    db.add(user)
    db.commit()


def list_billing(db: Session, user_id: int, *, limit: int = 20, offset: int = 0):
    """Subscription payments for one account - the receipt history."""
    filters = [
        Transaction.user_id == user_id,
        Transaction.kind == TransactionKind.subscription,
    ]
    items = list(
        db.scalars(
            select(Transaction)
            .where(*filters)
            .order_by(Transaction.created_at.desc(), Transaction.id.desc())
            .limit(limit)
            .offset(offset)
        )
    )
    total_paid = int(
        db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                *filters, Transaction.status == TransactionStatus.completed
            )
        )
        or 0
    )
    total = int(db.scalar(select(func.count(Transaction.id)).where(*filters)) or 0)
    return items, total, total_paid
