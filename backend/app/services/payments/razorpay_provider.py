"""Razorpay integration.

Orders are created through Razorpay's REST API with the key pair, and webhooks
are authenticated with the HMAC-SHA256 signature Razorpay sends in the
`X-Razorpay-Signature` header. A subscription is never activated from the
browser: only this verified webhook path can do it.
"""

import hashlib
import hmac
import json
from typing import Any, Mapping

import httpx

from ...config import settings
from .base import PaymentError, PaymentEvent, PaymentOrder

API_BASE = "https://api.razorpay.com/v1"


class RazorpayProvider:
    name = "razorpay"

    def is_configured(self) -> bool:
        return bool(settings.razorpay_key_id and settings.razorpay_key_secret)

    def create_order(
        self,
        *,
        user_id: int,
        amount_paise: int,
        currency: str = "INR",
        receipt: str = "",
    ) -> PaymentOrder:
        if not self.is_configured():
            raise PaymentError(
                "Razorpay is not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET."
            )

        payload = {
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt or f"skillearn-user-{user_id}",
            # The webhook reads the user id back from these notes.
            "notes": {"user_id": str(user_id), "product": "skillearn-subscription"},
        }
        try:
            response = httpx.post(
                f"{API_BASE}/orders",
                json=payload,
                auth=(settings.razorpay_key_id, settings.razorpay_key_secret),
                timeout=15.0,
            )
        except httpx.HTTPError as exc:
            raise PaymentError("Could not reach Razorpay. Please try again.") from exc

        if response.status_code >= 400:
            raise PaymentError("Razorpay refused the payment order. Please try again.")

        data = response.json()
        return PaymentOrder(
            provider=self.name,
            order_id=str(data["id"]),
            amount_paise=int(data.get("amount", amount_paise)),
            currency=str(data.get("currency", currency)),
            key_id=settings.razorpay_key_id,
            checkout_payload={"order_id": data["id"], "key_id": settings.razorpay_key_id},
        )

    def verify_webhook(self, *, body: bytes, headers: Mapping[str, str]) -> PaymentEvent:
        if not settings.razorpay_webhook_secret:
            raise PaymentError("RAZORPAY_WEBHOOK_SECRET is not set, so webhooks are rejected.")

        signature = headers.get("x-razorpay-signature") or ""
        expected = hmac.new(
            settings.razorpay_webhook_secret.encode(), body, hashlib.sha256
        ).hexdigest()
        if not signature or not hmac.compare_digest(signature, expected):
            raise PaymentError("The Razorpay webhook signature does not match.")

        try:
            payload: dict[str, Any] = json.loads(body or b"{}")
        except json.JSONDecodeError as exc:
            raise PaymentError("The webhook body is not valid JSON.") from exc

        payload_data = payload.get("payload") or {}
        payment = (payload_data.get("payment") or {}).get("entity") or {}
        order = (payload_data.get("order") or {}).get("entity") or {}
        entity = payment or order
        if not isinstance(entity, dict):
            entity = {}
        notes = entity.get("notes")
        notes = notes if isinstance(notes, dict) else {}
        try:
            user_id = int(notes.get("user_id", ""))
        except (TypeError, ValueError) as exc:
            raise PaymentError("The webhook does not carry a Learnora user id.") from exc

        order_id = str(entity.get("order_id") or entity.get("id") or "")
        if not order_id:
            raise PaymentError("The webhook does not reference an order.")

        event_name = str(payload.get("event") or "")
        paid = event_name in {"payment.captured", "order.paid"} or str(
            entity.get("status", "")
        ).lower() in {"captured", "paid"}

        # The receipt names what was bought: `course-<id>`, or nothing for the
        # subscription. It lives on the order, and Razorpay copies order notes
        # onto the payment entity.
        receipt = ""
        for source in (notes, order, payment):
            if isinstance(source, dict) and source.get("receipt"):
                receipt = str(source["receipt"])
                break

        return PaymentEvent(
            provider=self.name,
            order_id=order_id,
            amount_paise=int(entity.get("amount") or 0),
            user_id=user_id,
            paid=paid,
            payment_ref=entity.get("id"),
            note=f"Razorpay {event_name or 'payment'} for {order_id}",
            receipt=receipt,
        )


razorpay_provider = RazorpayProvider()
