"""Paid courses: who owns what, and how a course gets unlocked.

A course with `price_paise > 0` is closed until the learner pays for it:

* lessons withhold their notes and video from the public payload
* assessments open once the course is owned - a subscription is no longer needed
  for a course the learner has already paid for

There are two ways to pay. A gateway order (`start_checkout`) is fulfilled only
by the provider's signed webhook (`fulfil_payment`); a wallet purchase spends
earned rewards and is debited by the server itself. Both end in the same
`course_purchases` entitlement and both write one negative ledger row - either
`course_payment` (gateway money) or `course_purchase` (wallet money).
"""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    Course,
    CoursePurchase,
    Task,
    Transaction,
    TransactionKind,
    TransactionStatus,
    User,
)
from ..utils import format_paise, utcnow
from . import ledger
from .payments import PaymentError, PaymentEvent, PaymentOrder, get_payment_provider

#: Orders for a course carry `course-<id>` as their receipt, so the webhook can
#: tell which course was paid for without storing orders on our side.
RECEIPT_PREFIX = "course-"


class PurchaseError(Exception):
    """A purchase or a view that has to be refused. `status_code` maps to HTTP."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def get(db: Session, user_id: int, course_id: int) -> CoursePurchase | None:
    """The entitlement row, active or expired."""
    return db.scalars(
        select(CoursePurchase).where(
            CoursePurchase.user_id == user_id, CoursePurchase.course_id == course_id
        )
    ).first()


def receipt_for(course_id: int) -> str:
    """The receipt a gateway order carries so the webhook names its course."""
    return f"{RECEIPT_PREFIX}{course_id}"


def course_id_from_receipt(receipt: str) -> int | None:
    """The course an order was for, or None when it was not a course order."""
    text = (receipt or "").strip()
    if not text.startswith(RECEIPT_PREFIX):
        return None
    try:
        return int(text[len(RECEIPT_PREFIX) :])
    except ValueError:
        return None


def active(db: Session, user_id: int, course_id: int) -> CoursePurchase | None:
    purchase = get(db, user_id, course_id)
    return purchase if purchase is not None and purchase.is_active else None


def viewer_access(
    db: Session, user: User | None, course: Course
) -> tuple[bool, datetime | None]:
    """(may this reader open the course, when does their access lapse).

    Free courses are open to everyone; a paid one needs a purchase. Admins author
    the catalogue, so they can always preview what they built.
    """
    if course.price_paise <= 0:
        return True, None
    if user is None:
        return False, None
    if user.is_admin:
        return True, None
    purchase = active(db, user.id, course.id)
    if purchase is None:
        return False, None
    return True, purchase.expires_at


def has_access(db: Session, user: User | None, course: Course) -> bool:
    return viewer_access(db, user, course)[0]


def require_access(db: Session, user: User | None, course: Course) -> None:
    if has_access(db, user, course):
        return
    raise PurchaseError(
        f"Buy “{course.title}” to open this course. Every lesson and assessment "
        "unlocks with one payment.",
        402,
    )


def assert_task_access(db: Session, user: User, task: Task) -> None:
    """The gate the assessment routes call.

    A paid course is unlocked by its purchase; a free course still needs the
    subscription that pays for the assessments.
    """
    course = task.topic.course
    if course.price_paise > 0:
        if has_access(db, user, course):
            return
        raise PurchaseError(
            f"Buy “{course.title}” to unlock its assessments. A subscription alone "
            "does not open a paid course.",
            402,
        )

    if not user.has_active_subscription:
        raise PurchaseError(
            "An active subscription is required to unlock tasks. Subscribe to continue.",
            402,
        )


def assert_buyable(db: Session, *, user: User, course: Course) -> int:
    """The price in paise, or the reason this learner cannot buy it right now."""
    if not course.is_published:
        raise PurchaseError("That course is not available yet.", 404)

    price = max(course.price_paise, 0)
    if price <= 0:
        raise PurchaseError("This course is free to read - there is nothing to buy.", 409)

    if active(db, user.id, course.id) is not None:
        raise PurchaseError("You already own this course.", 409)

    return price


def _open(db: Session, *, user: User, course: Course, amount_paise: int) -> CoursePurchase:
    """Grant (or renew) the entitlement row. The caller commits."""
    expires_at = utcnow() + timedelta(days=course.access_days) if course.access_days else None
    purchase = get(db, user.id, course.id)
    if purchase is None:
        purchase = CoursePurchase(
            user_id=user.id,
            course_id=course.id,
            amount_paise=amount_paise,
            expires_at=expires_at,
        )
        db.add(purchase)
    else:
        purchase.amount_paise = amount_paise
        purchase.purchased_at = utcnow()
        purchase.expires_at = expires_at
    return purchase


def purchase_course(db: Session, *, user: User, course: Course) -> CoursePurchase:
    """Debit the wallet and (re)open the course for this learner.

    Refuses before writing anything, so a failed purchase never leaves a ledger
    row behind.
    """
    price = assert_buyable(db, user=user, course=course)

    balance = ledger.wallet_balance(db, user.id)
    if balance < price:
        short = price - balance
        raise PurchaseError(
            "Your wallet balance is too low for this course. You need "
            f"{format_paise(short)} more - rewards you earn are added to the "
            "same wallet.",
            402,
        )

    # One negative row per payment; the ledger stays the audit trail even when the
    # entitlement row below is reused for a renewal.
    ledger.add_transaction(
        db,
        user_id=user.id,
        kind=TransactionKind.course_purchase,
        amount=-price,
        status=TransactionStatus.completed,
        note=f"Course purchase: {course.title}",
        course_id=course.id,
    )

    purchase = _open(db, user=user, course=course, amount_paise=price)
    db.commit()
    db.refresh(purchase)
    return purchase


def start_checkout(db: Session, *, user: User, course: Course) -> PaymentOrder:
    """Open a gateway order for one course.

    Nothing is granted here: the price comes from the database (never from the
    browser) and the course opens only when the signed webhook comes back.
    """
    price = assert_buyable(db, user=user, course=course)

    provider = get_payment_provider()
    if not provider.is_configured():
        raise PurchaseError(
            "Payments are not set up on this server yet. Configure the payment "
            "provider and try again.",
            503,
        )

    try:
        return provider.create_order(
            user_id=user.id,
            amount_paise=price,
            currency="INR",
            receipt=receipt_for(course.id),
        )
    except PaymentError as exc:
        raise PurchaseError(str(exc), 502) from exc


def _record(
    db: Session, *, user: User, course: Course, amount_paise: int, provider_ref: str
) -> bool:
    """Write the revenue row and the entitlement, at most once per gateway order."""
    already = db.scalar(
        select(Transaction.id).where(Transaction.provider_ref == provider_ref)
    )
    if already is not None:
        return False

    ledger.add_transaction(
        db,
        user_id=user.id,
        kind=TransactionKind.course_payment,
        amount=-amount_paise,
        status=TransactionStatus.completed,
        note=f"Course payment: {course.title}",
        course_id=course.id,
        provider_ref=provider_ref,
    )
    _open(db, user=user, course=course, amount_paise=amount_paise)

    try:
        db.commit()
    except IntegrityError:
        # A concurrent webhook for the same order won the race. Let it stand.
        db.rollback()
        return False
    return True


def fulfil_payment(db: Session, event: PaymentEvent) -> bool:
    """Turn a *verified* gateway event into a course entitlement.

    Returns True only when this call unlocked something. A webhook that does not
    name a course, or names one we no longer teach, is ignored rather than
    failed - the gateway would otherwise retry it forever.
    """
    if not event.paid:
        return False

    course_id = course_id_from_receipt(event.receipt)
    if course_id is None:
        return False

    course = db.get(Course, course_id)
    if course is None or course.price_paise <= 0:
        return False

    user = db.get(User, event.user_id)
    if user is None:
        raise PurchaseError("That payment does not belong to a Learnora account.", 400)

    price = max(course.price_paise, 0)
    if event.amount_paise < price:
        raise PurchaseError(
            "The payment is smaller than the course price, so nothing was unlocked.",
            400,
        )

    return _record(
        db,
        user=user,
        course=course,
        amount_paise=event.amount_paise or price,
        provider_ref=event.order_id,
    )


def list_mine(db: Session, user_id: int) -> list[tuple[CoursePurchase, Course]]:
    """Everything this learner has bought, newest first."""
    rows = db.execute(
        select(CoursePurchase, Course)
        .join(Course, Course.id == CoursePurchase.course_id)
        .where(CoursePurchase.user_id == user_id)
        .order_by(CoursePurchase.purchased_at.desc(), CoursePurchase.id.desc())
    ).all()
    return [(purchase, course) for purchase, course in rows]
