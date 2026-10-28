"""Buying a course, and the courses already owned.

Two ways to pay for a course, both landing in the same entitlement:

* a gateway order (`/courses/{id}/checkout`), fulfilled only by the provider's
  signed webhook - the browser never grants anything itself
* the wallet balance, which holds earned rewards, debited by the server

The mock provider stands in for the gateway in development, and still sends its
"payment" through the same signature check the live gateway uses.
"""

import json
import uuid

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from ..config import settings
from ..deps import CurrentUser, DbSession
from ..schemas import CourseCheckoutOut, ErrorResponse, MyCourseOut, PurchaseOut
from ..services import catalog, ledger
from ..services import purchases as purchase_service
from ..services.payments import PaymentError, get_payment_provider
from ..services.purchases import PurchaseError

router = APIRouter(tags=["courses"])

_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="We could not find that course in the Learnora catalogue.",
)


class SimulatePaymentRequest(BaseModel):
    order_id: str = Field(min_length=3, max_length=120)


@router.post(
    "/courses/{course_id}/purchase",
    response_model=PurchaseOut,
    status_code=status.HTTP_201_CREATED,
    summary="Unlock a paid course with your wallet balance",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        402: {"model": ErrorResponse, "description": "Wallet balance too low"},
        404: {"model": ErrorResponse, "description": "No such course"},
        409: {"model": ErrorResponse, "description": "Already owned, or free"},
    },
)
def purchase_course(course_id: int, db: DbSession, user: CurrentUser) -> PurchaseOut:
    course = catalog.get_course(db, course_id)
    if course is None:
        raise _NOT_FOUND

    try:
        purchase = purchase_service.purchase_course(db, user=user, course=course)
    except PurchaseError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return PurchaseOut(
        course_id=course.id,
        amount_paise=purchase.amount_paise,
        purchased_at=purchase.purchased_at,
        expires_at=purchase.expires_at,
        balance_paise=ledger.wallet_balance(db, user.id),
        message=f"“{course.title}” is unlocked. Every lesson and assessment is open.",
    )


@router.post(
    "/courses/{course_id}/checkout",
    response_model=CourseCheckoutOut,
    status_code=status.HTTP_201_CREATED,
    summary="Start a payment for one course",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "No such course"},
        409: {"model": ErrorResponse, "description": "Already owned, or free"},
        502: {"model": ErrorResponse, "description": "The provider refused the order"},
        503: {"model": ErrorResponse, "description": "Payment provider not configured"},
    },
)
def start_course_checkout(course_id: int, db: DbSession, user: CurrentUser) -> CourseCheckoutOut:
    course = catalog.get_course(db, course_id)
    if course is None:
        raise _NOT_FOUND

    try:
        order = purchase_service.start_checkout(db, user=user, course=course)
    except PurchaseError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return CourseCheckoutOut(
        course_id=course.id,
        order_id=order.order_id,
        amount_paise=order.amount_paise,
        currency=order.currency,
        provider=order.provider,
        key_id=order.key_id,
        mock_payment_url=(
            f"/api/v1/courses/{course.id}/dev/simulate-payment"
            if order.provider == "mock" and not settings.is_prod
            else None
        ),
    )


@router.post(
    "/courses/payments/webhook",
    summary="Provider callback - the only path that unlocks a paid course",
    responses={400: {"model": ErrorResponse, "description": "Signature rejected"}},
)
async def course_payment_webhook(db: DbSession, request: Request) -> dict[str, object]:
    body = await request.body()
    provider = get_payment_provider()

    try:
        event = provider.verify_webhook(body=body, headers=dict(request.headers))
    except PaymentError as exc:
        # Unsigned or tampered webhooks are rejected outright.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        unlocked = purchase_service.fulfil_payment(db, event)
    except PurchaseError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    # 200 for duplicates too, so the provider stops retrying.
    return {"status": "ok", "unlocked": unlocked}


@router.post(
    "/courses/{course_id}/dev/simulate-payment",
    summary="Development only: pretend the gateway confirmed a course payment",
    responses={404: {"model": ErrorResponse, "description": "Not available"}},
)
def simulate_course_payment(
    course_id: int, payload: SimulatePaymentRequest, db: DbSession, user: CurrentUser
) -> dict[str, object]:
    """Stands in for the gateway when `PAYMENT_PROVIDER=mock` and `ENV=dev`.

    The amount and the receipt come from the server - never from the request -
    and the body is signed and verified exactly like a real callback, so the
    production path stays exercised.
    """
    provider = get_payment_provider()
    if settings.is_prod or provider.name != "mock":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")

    from ..services.payments.mock import sign, user_id_from_order

    if user_id_from_order(payload.order_id) != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="That payment order belongs to a different account.",
        )

    course = catalog.get_course(db, course_id)
    if course is None or course.price_paise <= 0:
        raise _NOT_FOUND

    body = json.dumps(
        {
            "order_id": payload.order_id,
            "amount_paise": course.price_paise,
            "status": "captured",
            "payment_id": f"mock_pay_{uuid.uuid4().hex[:12]}",
            "receipt": purchase_service.receipt_for(course.id),
        }
    ).encode()

    try:
        event = provider.verify_webhook(body=body, headers={"x-mock-signature": sign(body)})
    except PaymentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        unlocked = purchase_service.fulfil_payment(db, event)
    except PurchaseError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return {"status": "ok", "unlocked": unlocked}


@router.get(
    "/me/courses",
    response_model=list[MyCourseOut],
    summary="Courses you have unlocked",
)
def read_my_courses(db: DbSession, user: CurrentUser) -> list[MyCourseOut]:
    return [
        MyCourseOut(
            course_id=course.id,
            title=course.title,
            category=course.category,
            cover_image_url=course.cover_image_url,
            level=course.level,
            amount_paise=purchase.amount_paise,
            purchased_at=purchase.purchased_at,
            expires_at=purchase.expires_at,
            is_active=purchase.is_active,
        )
        for purchase, course in purchase_service.list_mine(db, user.id)
    ]
