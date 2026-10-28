"""Development-only provider.

No real money moves. It exists so the whole flow (order -> payment -> webhook ->
subscription) can be exercised locally. It is refused when `ENV=prod`.

The order id carries the user id so the webhook can rebuild the event without
storing orders: `mock_<user_id>_<random>`.
"""

import hashlib
import hmac
import json
import uuid
from typing import Any, Mapping

from ...config import settings
from .base import PaymentError, PaymentEvent, PaymentOrder

ORDER_PREFIX = "mock"


def _secret() -> str:
    return settings.razorpay_webhook_secret or "skillearn-mock-webhook-secret"


def sign(body: bytes) -> str:
    """Signature a simulated gateway would send in the `x-mock-signature` header."""
    return hmac.new(_secret().encode(), body, hashlib.sha256).hexdigest()


def user_id_from_order(order_id: str) -> int | None:
    parts = order_id.split("_")
    if len(parts) < 3 or parts[0] != ORDER_PREFIX:
        return None
    try:
        return int(parts[1])
    except ValueError:
        return None


class MockPaymentProvider:
    name = ORDER_PREFIX

    def is_configured(self) -> bool:
        return not settings.is_prod

    def create_order(
        self,
        *,
        user_id: int,
        amount_paise: int,
        currency: str = "INR",
        receipt: str = "",
    ) -> PaymentOrder:
        if settings.is_prod:
            raise PaymentError("The mock payment provider is disabled in production.")

        order_id = f"{ORDER_PREFIX}_{user_id}_{uuid.uuid4().hex[:12]}"
        return PaymentOrder(
            provider=self.name,
            order_id=order_id,
            amount_paise=amount_paise,
            currency=currency,
            key_id=None,
            checkout_payload={"mock": True, "receipt": receipt},
        )

    def verify_webhook(self, *, body: bytes, headers: Mapping[str, str]) -> PaymentEvent:
        signature = headers.get("x-mock-signature") or ""
        expected = sign(body)
        if not signature or not hmac.compare_digest(signature, expected):
            raise PaymentError("The mock webhook signature does not match.")

        try:
            payload: dict[str, Any] = json.loads(body or b"{}")
        except json.JSONDecodeError as exc:
            raise PaymentError("The webhook body is not valid JSON.") from exc

        order_id = str(payload.get("order_id") or "")
        user_id = user_id_from_order(order_id)
        if user_id is None:
            raise PaymentError("The webhook does not reference a Learnora order.")

        try:
            amount_paise = int(payload.get("amount_paise") or 0)
        except (TypeError, ValueError) as exc:
            raise PaymentError("The webhook amount is not a number.") from exc

        status = str(payload.get("status") or "captured").lower()
        return PaymentEvent(
            provider=self.name,
            order_id=order_id,
            amount_paise=amount_paise,
            user_id=user_id,
            paid=status in {"captured", "paid", "succeeded", "success"},
            payment_ref=payload.get("payment_id"),
            note=f"Mock payment via {order_id}",
            receipt=str(payload.get("receipt") or ""),
        )


mock_provider = MockPaymentProvider()
