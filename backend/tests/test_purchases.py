"""Paid courses: the lock, the wallet purchase, and what a purchase unlocks."""

from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import (
    Course,
    CoursePurchase,
    Task,
    TaskType,
    Topic,
    Transaction,
    TransactionKind,
    User,
)
from app.services import ledger
from app.services.settings_store import update_settings
from app.utils import utcnow

from conftest import API


@pytest.fixture(autouse=True)
def _no_limits(db):
    """Cooldown and rate limiting are covered elsewhere; keep these tests fast."""
    update_settings(
        db,
        {"attempt_cooldown_seconds": 0, "submission_rate_limit_per_minute": 600},
        updated_by=None,
    )


def _seed_paid_course(
    db, *, price: int = 20000, access_days: int | None = None
) -> tuple[Course, Task]:
    """A published course with one quiz and no video, so only access gates it."""
    course = Course(
        title="Paid Python",
        category="Python",
        description="",
        is_published=True,
        price_paise=price,
        access_days=access_days,
    )
    db.add(course)
    db.flush()

    topic = Topic(course_id=course.id, title="Basics", content="## Secret notes", position=0)
    db.add(topic)
    db.flush()

    task = Task(
        topic_id=topic.id,
        title="Basics check",
        type=TaskType.quiz,
        pass_percent=60,
        reward=1000,
        is_active=True,
        config={
            "questions": [
                {"id": "q1", "prompt": "1 + 1", "options": ["1", "2"], "correct_index": 1}
            ]
        },
    )
    db.add(task)
    db.commit()
    db.refresh(course)
    db.refresh(task)
    return course, task


def _credit(db, email: str, paise: int) -> None:
    """A reward row, so the wallet has a balance to spend."""
    user = db.scalar(select(User).where(User.email == email))
    ledger.add_transaction(
        db,
        user_id=user.id,
        kind=TransactionKind.reward,
        amount=paise,
        note="Test credit",
    )
    db.commit()


def test_a_paid_lesson_withholds_its_material(client, db):
    course, task = _seed_paid_course(db)

    topic = client.get(f"{API}/topics/{task.topic_id}").json()
    assert topic["is_locked"] is True
    assert topic["content"] == ""
    assert topic["video_url"] is None
    assert topic["course_price_paise"] == 20000
    assert topic["requires_subscription"] is False
    # The task list itself is still visible: it is the shop window.
    assert topic["tasks"][0]["title"] == "Basics check"

    detail = client.get(f"{API}/courses/{course.id}").json()
    assert detail["has_access"] is False
    assert detail["price_paise"] == 20000


def test_purchase_is_refused_without_a_wallet_balance(client, db, auth_headers):
    course, _ = _seed_paid_course(db)
    headers = auth_headers()

    refused = client.post(f"{API}/courses/{course.id}/purchase", headers=headers)
    assert refused.status_code == 402
    assert "wallet" in refused.json()["detail"].lower()

    # Nothing was written: no entitlement and no ledger row.
    assert db.scalar(select(CoursePurchase)) is None
    assert (
        db.scalar(select(Transaction).where(Transaction.kind == TransactionKind.course_purchase))
        is None
    )


def test_buying_debits_the_wallet_and_unlocks_the_course(client, db, auth_headers):
    course, task = _seed_paid_course(db)
    headers = auth_headers()
    _credit(db, "learner@example.com", 25000)

    bought = client.post(f"{API}/courses/{course.id}/purchase", headers=headers)
    assert bought.status_code == 201, bought.text
    body = bought.json()
    assert body["amount_paise"] == 20000
    assert body["balance_paise"] == 5000
    # A blank `access_days` means the purchase never expires.
    assert body["expires_at"] is None

    user = db.scalar(select(User).where(User.email == "learner@example.com"))
    assert ledger.wallet_balance(db, user.id) == 5000
    row = db.scalar(
        select(Transaction).where(Transaction.kind == TransactionKind.course_purchase)
    )
    assert row.amount == -20000
    assert row.course_id == course.id

    topic = client.get(f"{API}/topics/{task.topic_id}", headers=headers).json()
    assert topic["is_locked"] is False
    assert topic["content"] == "## Secret notes"

    detail = client.get(f"{API}/courses/{course.id}", headers=headers).json()
    assert detail["has_access"] is True

    # A course the learner paid for does not also demand a subscription.
    quiz = client.get(f"{API}/tasks/{task.id}/quiz", headers=headers)
    assert quiz.status_code == 200, quiz.text


def test_a_course_is_charged_once(client, db, auth_headers):
    course, _ = _seed_paid_course(db)
    headers = auth_headers()
    _credit(db, "learner@example.com", 50000)

    assert client.post(f"{API}/courses/{course.id}/purchase", headers=headers).status_code == 201
    second = client.post(f"{API}/courses/{course.id}/purchase", headers=headers)
    assert second.status_code == 409

    user = db.scalar(select(User).where(User.email == "learner@example.com"))
    assert ledger.wallet_balance(db, user.id) == 30000


def test_a_free_course_cannot_be_bought(client, db, auth_headers):
    course, _ = _seed_paid_course(db, price=0)

    refused = client.post(f"{API}/courses/{course.id}/purchase", headers=auth_headers())
    assert refused.status_code == 409


def test_expired_access_locks_the_course_again(client, db, auth_headers):
    course, task = _seed_paid_course(db, access_days=30)
    headers = auth_headers()
    _credit(db, "learner@example.com", 25000)

    bought = client.post(f"{API}/courses/{course.id}/purchase", headers=headers)
    assert bought.status_code == 201, bought.text
    assert bought.json()["expires_at"] is not None

    purchase = db.scalar(select(CoursePurchase))
    purchase.expires_at = utcnow() - timedelta(days=1)
    db.commit()

    topic = client.get(f"{API}/topics/{task.topic_id}", headers=headers).json()
    assert topic["is_locked"] is True
    assert client.get(f"{API}/tasks/{task.id}/quiz", headers=headers).status_code == 402
