"""Schemas for buying a course and for the list of courses already owned."""

from datetime import datetime

from pydantic import BaseModel

from ..models import CourseLevel


class PurchaseOut(BaseModel):
    """The receipt the browser shows right after a purchase."""

    course_id: int
    amount_paise: int
    purchased_at: datetime
    expires_at: datetime | None
    #: The wallet balance *after* the debit, so the header updates immediately.
    balance_paise: int
    message: str


class CourseCheckoutOut(BaseModel):
    """What the browser needs in order to pay for one course."""

    course_id: int
    order_id: str
    amount_paise: int
    currency: str
    provider: str
    key_id: str | None = None
    #: Only populated by the mock provider in development.
    mock_payment_url: str | None = None


class MyCourseOut(BaseModel):
    """One course this learner has unlocked."""

    course_id: int
    title: str
    category: str
    cover_image_url: str | None
    level: CourseLevel
    amount_paise: int
    purchased_at: datetime
    expires_at: datetime | None
    is_active: bool
