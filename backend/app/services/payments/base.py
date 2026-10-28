"""The payment provider contract.

Everything above this layer only knows about `PaymentOrder` and `PaymentEvent`,
so Razorpay can be swapped for another gateway without touching the routers.
"""

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol


class PaymentError(Exception):
    """Raised when the gateway refuses a request or a webhook cannot be trusted."""


@dataclass(frozen=True)
class PaymentOrder:
    provider: str
    order_id: str
    amount_paise: int
    currency: str = "INR"
    key_id: str | None = None
    checkout_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PaymentEvent:
    """A payment outcome we are willing to trust, after signature verification."""

    provider: str
    order_id: str
    amount_paise: int
    user_id: int
    paid: bool
    payment_ref: str | None = None
    note: str = ""
    #: Echoes the receipt the order was created with, so one webhook can tell a
    #: subscription (empty) from a course (`course-<id>`).
    receipt: str = ""


class PaymentProvider(Protocol):
    name: str

    def is_configured(self) -> bool: ...

    def create_order(
        self,
        *,
        user_id: int,
        amount_paise: int,
        currency: str = "INR",
        receipt: str = "",
    ) -> PaymentOrder: ...

    def verify_webhook(self, *, body: bytes, headers: Mapping[str, str]) -> PaymentEvent:
        """Verify the gateway signature and return the trusted event.

        Must raise `PaymentError` when the signature is missing or wrong.
        """
        ...
