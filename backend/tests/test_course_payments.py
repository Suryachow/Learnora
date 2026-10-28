"""Paying for a course through the (mock) payment gateway.

The browser starts an order and nothing more. A course opens only when a
signature-verified webhook says the payment was captured, and a replayed webhook
never charges or unlocks twice.
"""

import json

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
from app.services.payments.mock import sign
from app.services.settings_store import update_settings

from conftest import API


@pytest.fixture(autouse=True)
def _no_limits(db):
    """Cooldown and rate limiting are covered elsewhere; keep these tests fast."""
    update_settings(
        db,
        {"attempt_cooldown_seconds": 0, "submission_rate_limit_per_minute": 600},
        updated_by=None,
    )


def _seed_paid_course(db, *, price: int = 45000) -> tuple[Course, Task]:
    """A published, priced course with one quiz and no video."""
    course = Course(
        title="C Programming",
        category="C",
        description="",
        is_published=True,
        price_paise=price,
    )
    db.add(course)
    db.flush()

    topic = Topic(course_id=course.id, title="Pointers", content="## Secret notes", position=0)
    db.add(topic)
    db.flush()

    task = Task(
        topic_id=topic.id,
        title="Pointers check",
        type=TaskType.quiz,
        pass_percent=60,
        reward=1000,
        is_active=True,
        config={
            "questions": [
                {
                    "id": "q1",
                    "prompt": "1 + 1",
                    "options": ["1", "2"],
                    "correct_index": 1,
                }
            ]
        },
    )
    db.add(task)
    db.commit()
    db.refresh(course)
    db.refresh(task)
    return course, task


def _signed(body: dict) -> tuple[bytes, dict[str, str]]:
    """The signed callback a gateway would POST for this event."""
    raw = json.dumps(body).encode()
    return raw, {"x-mock-signature": sign(raw), "content-type": "application/json"}


def test_checkout_prices_the_course_and_unlocks_nothing(client, db, auth_headers):
    course, _ = _seed_paid_course(db)

    started = client.post(f"{API}/courses/{course.id}/checkout", headers=auth_headers())
    assert started.status_code == 201, started.text
    order = started.json()

    # The price comes from the catalogue, never from the browser.
    assert order["amount_paise"] == 45000
    assert order["provider"] == "mock"
    assert order["mock_payment_url"].endswith(f"/courses/{course.id}/dev/simulate-payment")
    assert order["order_id"].startswith("mock_")

    # Starting a payment is not paying: nothing is owned and nothing is recorded.
    assert db.scalar(select(CoursePurchase)) is None
    assert db.scalar(select(Transaction)) is None


def test_confirming_the_payment_unlocks_the_course(client, db, auth_headers):
    course, task = _seed_paid_course(db)
    headers = auth_headers()

    order = client.post(f"{API}/courses/{course.id}/checkout", headers=headers).json()
    paid = client.post(
        f"{API}/courses/{course.id}/dev/simulate-payment",
        headers=headers,
        json={"order_id": order["order_id"]},
    )
    assert paid.status_code == 200, paid.text
    assert paid.json()["unlocked"] is True

    topic = client.get(f"{API}/topics/{task.topic_id}", headers=headers).json()
    assert topic["is_locked"] is False
    assert topic["content"] == "## Secret notes"

    # A paid-for course does not also demand a subscription.
    assert client.get(f"{API}/tasks/{task.id}/quiz", headers=headers).status_code == 200

    user = db.scalar(select(User).where(User.email == "learner@example.com"))
    row = db.scalar(select(Transaction))
    assert row.kind is TransactionKind.course_payment
    assert row.amount == -45000
    assert row.course_id == course.id
    assert row.provider_ref == order["order_id"]
    # Gateway money never moves the reward balance.
    assert ledger.wallet_balance(db, user.id) == 0
    assert ledger.course_revenue(db) == 45000


def test_a_replayed_payment_is_ignored(client, db, auth_headers):
    course, _ = _seed_paid_course(db)
    headers = auth_headers()
    order = client.post(f"{API}/courses/{course.id}/checkout", headers=headers).json()
    payload = {"order_id": order["order_id"]}

    first = client.post(
        f"{API}/courses/{course.id}/dev/simulate-payment", headers=headers, json=payload
    )
    second = client.post(
        f"{API}/courses/{course.id}/dev/simulate-payment", headers=headers, json=payload
    )

    assert first.json()["unlocked"] is True
    assert second.status_code == 200
    assert second.json()["unlocked"] is False
    assert len(db.scalars(select(Transaction)).all()) == 1
    assert len(db.scalars(select(CoursePurchase)).all()) == 1


def test_an_owned_course_is_not_sold_twice(client, db, auth_headers):
    course, _ = _seed_paid_course(db)
    headers = auth_headers()
    order = client.post(f"{API}/courses/{course.id}/checkout", headers=headers).json()
    client.post(
        f"{API}/courses/{course.id}/dev/simulate-payment",
        headers=headers,
        json={"order_id": order["order_id"]},
    )

    again = client.post(f"{API}/courses/{course.id}/checkout", headers=headers)
    assert again.status_code == 409


def test_a_free_course_cannot_be_paid_for(client, db, auth_headers):
    course, _ = _seed_paid_course(db, price=0)

    refused = client.post(f"{API}/courses/{course.id}/checkout", headers=auth_headers())
    assert refused.status_code == 409


def test_simulating_someone_elses_order_is_forbidden(client, db, auth_headers):
    course, _ = _seed_paid_course(db)
    mine = auth_headers()
    order = client.post(f"{API}/courses/{course.id}/checkout", headers=mine).json()

    theirs = auth_headers(email="other@example.com")
    refused = client.post(
        f"{API}/courses/{course.id}/dev/simulate-payment",
        headers=theirs,
        json={"order_id": order["order_id"]},
    )
    assert refused.status_code == 403
    assert db.scalar(select(CoursePurchase)) is None


def test_an_unsigned_webhook_is_rejected(client, db, auth_headers):
    course, _ = _seed_paid_course(db)
    headers = auth_headers()
    order = client.post(f"{API}/courses/{course.id}/checkout", headers=headers).json()

    body = json.dumps(
        {
            "order_id": order["order_id"],
            "amount_paise": 45000,
            "status": "captured",
            "receipt": f"course-{course.id}",
        }
    )
    refused = client.post(
        f"{API}/courses/payments/webhook",
        content=body,
        headers={"content-type": "application/json"},
    )
    assert refused.status_code == 400
    assert db.scalar(select(CoursePurchase)) is None


def test_a_short_payment_unlocks_nothing(client, db, auth_headers):
    course, _ = _seed_paid_course(db)
    headers = auth_headers()
    order = client.post(f"{API}/courses/{course.id}/checkout", headers=headers).json()

    body, signature = _signed(
        {
            "order_id": order["order_id"],
            "amount_paise": 100,
            "status": "captured",
            "receipt": f"course-{course.id}",
        }
    )
    refused = client.post(
        f"{API}/courses/payments/webhook", content=body, headers=signature
    )
    assert refused.status_code == 400
    assert db.scalar(select(CoursePurchase)) is None
    assert db.scalar(select(Transaction)) is None


def test_a_course_order_on_the_subscription_webhook_buys_no_subscription(client, db, auth_headers):
    """One callback URL for both products must not hand out free subscriptions."""
    course, task = _seed_paid_course(db)
    headers = auth_headers()
    order = client.post(f"{API}/courses/{course.id}/checkout", headers=headers).json()

    body, signature = _signed(
        {
            "order_id": order["order_id"],
            "amount_paise": 45000,
            "status": "captured",
            "receipt": f"course-{course.id}",
        }
    )
    handled = client.post(f"{API}/subscription/webhook", content=body, headers=signature)
    assert handled.status_code == 200, handled.text
    assert handled.json()["unlocked"] is True

    user = db.scalar(select(User).where(User.email == "learner@example.com"))
    assert user.has_active_subscription is False
    assert db.scalar(
        select(Transaction).where(Transaction.kind == TransactionKind.subscription)
    ) is None
    assert (
        client.get(f"{API}/topics/{task.topic_id}", headers=headers).json()["is_locked"] is False
    )
