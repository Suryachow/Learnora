"""Small shared helpers."""

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Naive UTC timestamp.

    All timestamps in Learnora are stored as *naive UTC* so that SQLite and
    PostgreSQL behave identically and comparisons never mix aware/naive values.
    """
    return datetime.now(UTC).replace(tzinfo=None)


def format_paise(amount: int) -> str:
    """Render integer paise as a rupee string, e.g. 14900 -> '₹149.00'."""
    sign = "-" if amount < 0 else ""
    rupees, paise = divmod(abs(amount), 100)
    return f"{sign}₹{rupees:,}.{paise:02d}"
