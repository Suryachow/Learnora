"""The assessment flow: subscription gate, server-side grading, reward payout."""

from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import Course, Task, TaskType, Topic, User
from app.services.ledger import wallet_balance
from app.services.settings_store import update_settings
from app.utils import utcnow

from conftest import API


def _seed_quiz(db, *, reward: int = 2000, pass_percent: int = 60) -> Task:
    course = Course(title="Python", category="Python", description="", is_published=True)
    db.add(course)
    db.flush()
    topic = Topic(course_id=course.id, title="Basics", content="", position=0)
    db.add(topic)
    db.flush()
    task = Task(
        topic_id=topic.id,
        title="Basics check",
        type=TaskType.quiz,
        pass_percent=pass_percent,
        reward=reward,
        is_active=True,
        config={
            "questions": [
                {"id": "q1", "prompt": "1 + 1", "options": ["1", "2", "3"], "correct_index": 1},
                {"id": "q2", "prompt": "2 + 2", "options": ["3", "4", "5"], "correct_index": 1},
            ]
        },
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def _subscribe(db, email: str = "learner@example.com") -> User:
    user = db.scalar(select(User).where(User.email == email))
    user.subscribed_until = utcnow() + timedelta(days=30)
    db.commit()
    return user


@pytest.fixture(autouse=True)
def _no_limits(db):
    """Cooldown and rate limiting are tested implicitly; keep other tests fast."""
    update_settings(
        db,
        {"attempt_cooldown_seconds": 0, "submission_rate_limit_per_minute": 600},
        updated_by=None,
    )


def test_quiz_requires_a_subscription(client, db, auth_headers):
    task = _seed_quiz(db)
    headers = auth_headers()

    blocked = client.get(f"{API}/tasks/{task.id}/quiz", headers=headers)
    assert blocked.status_code == 402

    blocked_submit = client.post(
        f"{API}/tasks/{task.id}/attempts", json={"answers": {}}, headers=headers
    )
    assert blocked_submit.status_code == 402


def test_quiz_never_leaks_the_answers(client, db, auth_headers):
    task = _seed_quiz(db)
    headers = auth_headers()
    _subscribe(db)

    response = client.get(f"{API}/tasks/{task.id}/quiz", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["pass_percent"] == 60
    assert len(body["questions"]) == 2
    for question in body["questions"]:
        assert "correct_index" not in question


def test_passing_once_pays_once(client, db, auth_headers):
    task = _seed_quiz(db, reward=2000)
    headers = auth_headers()
    user = _subscribe(db)

    first = client.post(
        f"{API}/tasks/{task.id}/attempts",
        json={"answers": {"q1": 1, "q2": 1}},
        headers=headers,
    )
    assert first.status_code == 201, first.text
    body = first.json()
    assert body["passed"] is True
    assert body["percent"] == 100
    assert body["correct_count"] == 2
    assert body["reward_granted"] is True
    assert body["reward_paise"] == 2000
    assert wallet_balance(db, user.id) == 2000

    second = client.post(
        f"{API}/tasks/{task.id}/attempts",
        json={"answers": {"q1": 1, "q2": 1}},
        headers=headers,
    )
    assert second.status_code == 201, second.text
    assert second.json()["reward_granted"] is False
    assert second.json()["reward_reason"] == "already_rewarded"
    # Still only one payout.
    assert wallet_balance(db, user.id) == 2000


def test_failing_scores_no_reward(client, db, auth_headers):
    task = _seed_quiz(db, reward=2000, pass_percent=90)
    headers = auth_headers()
    user = _subscribe(db)

    response = client.post(
        f"{API}/tasks/{task.id}/attempts",
        json={"answers": {"q1": 1, "q2": 0}},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["passed"] is False
    assert body["percent"] == 50
    assert body["reward_granted"] is False
    assert wallet_balance(db, user.id) == 0


def test_rewards_can_be_switched_off_globally(client, db, auth_headers):
    task = _seed_quiz(db, reward=2000)
    headers = auth_headers()
    user = _subscribe(db)
    update_settings(db, {"rewards_enabled": False}, updated_by=None)

    response = client.post(
        f"{API}/tasks/{task.id}/attempts",
        json={"answers": {"q1": 1, "q2": 1}},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    assert response.json()["reward_reason"] == "rewards_disabled"
    assert wallet_balance(db, user.id) == 0


def test_per_task_cap_limits_the_payout(client, db, auth_headers):
    task = _seed_quiz(db, reward=90000)
    headers = auth_headers()
    user = _subscribe(db)
    update_settings(db, {"reward_per_task_limit_paise": 3000}, updated_by=None)

    response = client.post(
        f"{API}/tasks/{task.id}/attempts",
        json={"answers": {"q1": 1, "q2": 1}},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    assert response.json()["reward_paise"] == 3000
    assert response.json()["reward_reason"] == "limit_capped"
    assert wallet_balance(db, user.id) == 3000


def test_attempt_history_is_the_users_own(client, db, auth_headers):
    task = _seed_quiz(db)
    headers = auth_headers()
    _subscribe(db)
    client.post(
        f"{API}/tasks/{task.id}/attempts",
        json={"answers": {"q1": 1, "q2": 1}},
        headers=headers,
    )

    response = client.get(f"{API}/me/attempts", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["task_title"] == "Basics check"
