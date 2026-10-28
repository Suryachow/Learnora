"""Payment providers."""

from ...config import settings
from .base import PaymentError, PaymentEvent, PaymentOrder, PaymentProvider
from .mock import MockPaymentProvider, mock_provider
from .razorpay_provider import RazorpayProvider, razorpay_provider

_PROVIDERS: dict[str, PaymentProvider] = {
    mock_provider.name: mock_provider,
    razorpay_provider.name: razorpay_provider,
}


def get_payment_provider() -> PaymentProvider:
    """The provider selected by `PAYMENT_PROVIDER`."""
    provider = _PROVIDERS.get(settings.payment_provider.strip().lower())
    if provider is None:
        raise PaymentError(
            f"Unknown payment provider {settings.payment_provider!r}. "
            "Use 'mock' for local development or 'razorpay'."
        )
    return provider


__all__ = [
    "MockPaymentProvider",
    "PaymentError",
    "PaymentEvent",
    "PaymentOrder",
    "PaymentProvider",
    "RazorpayProvider",
    "get_payment_provider",
    "mock_provider",
    "razorpay_provider",
]
