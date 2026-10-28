"""Subscription: plan, checkout, and the webhook that activates the plan.

The browser can *start* a payment, but only a signature-verified provider
webhook can activate a subscription. There is no endpoint that trusts a
browser's word that a payment succeeded - the mock simulation below still goes
through the same signature check as the real gateway.
"""

import json
import uuid

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from ..config import settings
from ..deps import CurrentUser, DbSession
from ..schemas import CheckoutResponse, ErrorResponse, PlanOut
from ..services import handle_payment_event
from ..services.payments import PaymentError, get_payment_provider
from ..services.purchases import PurchaseError, course_id_from_receipt, fulfil_payment
from ..services.settings_store import runtime_settings
from ..services.subscription import SubscriptionError, plan_details

router = APIRouter(prefix="/subscription", tags=["subscription"])


class SimulatePaymentRequest(BaseModel):
    order_id: str = Field(min_length=3, max_length=120)


@router.get("/plan", response_model=PlanOut, summary="Price and terms of the plan")
def read_plan(db: DbSession) -> PlanOut:
    return PlanOut(**plan_details(db))


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    summary="Create a payment order",
    responses={
        503: {"model": ErrorResponse, "description": "Payment provider not configured"},
    },
)
def create_checkout(db: DbSession, user: CurrentUser) -> CheckoutResponse:
    provider = get_payment_provider()
    if not provider.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Payments are not set up on this server yet. "
                "Configure the payment provider and try again."
            ),
        )

    try:
        order = provider.create_order(
            user_id=user.id,
            amount_paise=runtime_settings(db).subscription_price_paise,
            currency="INR",
            receipt=f"learnora-{user.id}",
        )
    except PaymentError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return CheckoutResponse(
        order_id=order.order_id,
        amount_paise=order.amount_paise,
        currency=order.currency,
        provider=order.provider,
        key_id=order.key_id,
        mock_payment_url=(
            "/api/v1/subscription/dev/simulate-payment"
            if order.provider == "mock" and not settings.is_prod
            else None
        ),
    )


@router.post(
    "/webhook",
    summary="Provider callback - the only path that activates a subscription",
    responses={400: {"model": ErrorResponse, "description": "Signature rejected"}},
)
async def payment_webhook(db: DbSession, request: Request) -> dict[str, object]:
    body = await request.body()
    provider = get_payment_provider()

    try:
        event = provider.verify_webhook(body=body, headers=dict(request.headers))
    except PaymentError as exc:
        # Unsigned or tampered webhooks are rejected outright.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        # A course order only reaches this endpoint when the gateway is set up
        # with one callback URL for both products, so send it where it belongs
        # instead of activating a subscription nobody paid for.
        if course_id_from_receipt(event.receipt) is not None:
            unlocked = fulfil_payment(db, event)
            return {"status": "ok", "activated": False, "unlocked": unlocked}
        activated = handle_payment_event(db, event)
    except (SubscriptionError, PurchaseError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    # 200 for duplicates too, so the provider stops retrying.
    return {"status": "ok", "activated": activated}


@router.post(
    "/dev/simulate-payment",
    summary="Development only: pretend the gateway confirmed the payment",
    responses={404: {"model": ErrorResponse, "description": "Not available"}},
)
def simulate_payment(
    payload: SimulatePaymentRequest, db: DbSession, user: CurrentUser
) -> dict[str, object]:
    """Stands in for the gateway when `PAYMENT_PROVIDER=mock` and `ENV=dev`.

    It builds the same signed webhook body a real gateway would send and runs it
    through the same verification code, so the production path stays exercised.
    """
    provider = get_payment_provider()
    if settings.is_prod or provider.name != "mock":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not found."
        )

    from ..services.payments.mock import sign, user_id_from_order

    if user_id_from_order(payload.order_id) != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="That payment order belongs to a different account.",
        )

    body = json.dumps(
        {
            "order_id": payload.order_id,
            "amount_paise": runtime_settings(db).subscription_price_paise,
            "status": "captured",
            "payment_id": f"mock_pay_{uuid.uuid4().hex[:12]}",
        }
    ).encode()

    try:
        event = provider.verify_webhook(body=body, headers={"x-mock-signature": sign(body)})
    except PaymentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    activated = handle_payment_event(db, event)
    return {"status": "ok", "activated": activated}
