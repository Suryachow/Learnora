"""The admin console API: the gate, catalogue CRUD, the quiz builder and settings."""

from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import Task, User
from app.services.settings_store import runtime_settings
from app.utils import utcnow

from conftest import API, PASSWORD


@pytest.fixture
def admin_headers(client, make_admin, login):
    make_admin()
    token = login(email="admin@example.com", password=PASSWORD)
    return {"Authorization": f"Bearer {token}"}


def test_admin_routes_are_closed_to_learners(client, auth_headers):
    response = client.get(f"{API}/admin/reports/overview", headers=auth_headers())
    assert response.status_code == 403


def test_admin_routes_reject_anonymous_callers(client):
    response = client.get(f"{API}/admin/settings")
    assert response.status_code == 401


def test_catalogue_crud_and_quiz_builder(client, admin_headers):
    course = client.post(
        f"{API}/admin/courses",
        json={
            "title": "Go Essentials",
            "category": "Go",
            "description": "Learn Go.",
            "is_published": True,
        },
        headers=admin_headers,
    )
    assert course.status_code == 201, course.text
    course_id = course.json()["id"]
    assert course.json()["topic_count"] == 0

    topic = client.post(
        f"{API}/admin/courses/{course_id}/topics",
        json={"title": "Goroutines", "content": "## Concurrency", "video_url": None},
        headers=admin_headers,
    )
    assert topic.status_code == 201, topic.text
    topic_id = topic.json()["id"]

    task = client.post(
        f"{API}/admin/tasks",
        json={
            "topic_id": topic_id,
            "title": "Concurrency check",
            "pass_percent": 60,
            "reward": 2500,
            "is_active": True,
            "questions": [
                {
                    "prompt": "Which keyword starts a goroutine?",
                    "options": ["async", "go", "spawn", "thread"],
                    "correct_index": 1,
                    "points": 1,
                }
            ],
        },
        headers=admin_headers,
    )
    assert task.status_code == 201, task.text
    task_id = task.json()["id"]
    assert task.json()["question_count"] == 1

    # An admin may see the answers, since they authored them.
    detail = client.get(f"{API}/admin/tasks/{task_id}", headers=admin_headers)
    assert detail.status_code == 200
    assert detail.json()["questions"][0]["correct_index"] == 1

    updated = client.patch(
        f"{API}/admin/tasks/{task_id}",
        json={"reward": 3000, "is_active": False},
        headers=admin_headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["reward"] == 3000
    assert updated.json()["is_active"] is False
    # The question set is untouched by a partial update.
    assert updated.json()["question_count"] == 1

    second = client.post(
        f"{API}/admin/courses/{course_id}/topics",
        json={"title": "Channels", "content": ""},
        headers=admin_headers,
    )
    reordered = client.post(
        f"{API}/admin/courses/{course_id}/topics/reorder",
        json={"ordered_ids": [second.json()["id"], topic_id]},
        headers=admin_headers,
    )
    assert reordered.status_code == 200
    assert reordered.json()[0]["id"] == second.json()["id"]

    deleted = client.delete(f"{API}/admin/courses/{course_id}", headers=admin_headers)
    assert deleted.status_code == 204


def test_course_creation_accepts_a_price_and_catalogue_detail(client, admin_headers):
    created = client.post(
        f"{API}/admin/courses",
        json={
            "title": "Data Visualisation",
            "category": "Data",
            "description": "Charts people can actually read.",
            "is_published": True,
            "price_paise": 249900,
            "cover_image_url": "https://example.com/cover.png",
            "level": "intermediate",
            "duration_minutes": 180,
            "outcomes": ["Choose the right chart", "  Trim this line  ", ""],
            "access_days": 90,
        },
        headers=admin_headers,
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["price_paise"] == 249900
    assert body["cover_image_url"] == "https://example.com/cover.png"
    assert body["level"] == "intermediate"
    assert body["duration_minutes"] == 180
    assert body["outcomes"] == ["Choose the right chart", "Trim this line"]
    assert body["access_days"] == 90
    assert body["purchase_count"] == 0

    # An update touches only what it sends, and an explicit null clears the
    # optional fields (permanent access, no cover image).
    patched = client.patch(
        f"{API}/admin/courses/{body['id']}",
        json={"access_days": None, "price_paise": 0},
        headers=admin_headers,
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["access_days"] is None
    assert patched.json()["price_paise"] == 0
    assert patched.json()["level"] == "intermediate"

    rejected = client.post(
        f"{API}/admin/courses",
        json={"title": "Negative price", "category": "Data", "price_paise": -1},
        headers=admin_headers,
    )
    assert rejected.status_code == 422


def test_settings_are_readable_and_editable(client, db, admin_headers):
    listing = client.get(f"{API}/admin/settings", headers=admin_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 9

    changed = client.patch(
        f"{API}/admin/settings",
        json={"values": {"subscription_price_paise": 19900}},
        headers=admin_headers,
    )
    assert changed.status_code == 200, changed.text
    price = next(row for row in changed.json() if row["key"] == "subscription_price_paise")
    assert price["value"] == 19900
    assert price["is_overridden"] is True
    assert runtime_settings(db).subscription_price_paise == 19900

    # The plan the browser sees picks the change up immediately.
    plan = client.get(f"{API}/subscription/plan")
    assert plan.json()["price_paise"] == 19900

    rejected = client.patch(
        f"{API}/admin/settings",
        json={"values": {"subscription_days": -5}},
        headers=admin_headers,
    )
    assert rejected.status_code == 422

    reset = client.post(
        f"{API}/admin/settings/subscription_price_paise/reset", headers=admin_headers
    )
    assert reset.status_code == 200
    price = next(row for row in reset.json() if row["key"] == "subscription_price_paise")
    assert price["is_overridden"] is False


def test_admin_can_manage_users(client, db, admin_headers):
    learner = client.post(
        f"{API}/auth/register",
        json={"name": "Learner", "email": "learner@example.com", "password": PASSWORD},
    )
    assert learner.status_code == 201, learner.text
    learner_id = learner.json()["user"]["id"]

    listing = client.get(f"{API}/admin/users?search=learner", headers=admin_headers)
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert listing.json()["items"][0]["wallet_balance_paise"] == 0

    granted = client.patch(
        f"{API}/admin/users/{learner_id}",
        json={"grant_subscription_days": 30},
        headers=admin_headers,
    )
    assert granted.status_code == 200, granted.text
    assert granted.json()["has_active_subscription"] is True

    revoked = client.patch(
        f"{API}/admin/users/{learner_id}",
        json={"revoke_subscription": True},
        headers=admin_headers,
    )
    assert revoked.status_code == 200
    assert revoked.json()["has_active_subscription"] is False


def test_report_overview_totals(client, db, admin_headers):
    learner = client.post(
        f"{API}/auth/register",
        json={"name": "Learner", "email": "learner@example.com", "password": PASSWORD},
    )
    learner_id = learner.json()["user"]["id"]
    user = db.scalar(select(User).where(User.id == learner_id))
    user.subscribed_until = utcnow() + timedelta(days=30)
    db.commit()

    client.post(
        f"{API}/admin/courses",
        json={"title": "Reports Course", "category": "Reports", "is_published": True},
        headers=admin_headers,
    )

    overview = client.get(f"{API}/admin/reports/overview", headers=admin_headers)
    assert overview.status_code == 200, overview.text
    body = overview.json()
    assert body["total_users"] == 2
    assert body["subscribed_users"] == 1
    assert body["course_count"] == 1
    assert body["rewards_enabled"] is True
    assert len(body["daily"]) == 30
    # The dashboard reads these, so they must always come back shaped.
    assert len(body["funnel"]) == 4
    assert body["growth"]["days"] == 30
    assert set(body["growth"]["current"]) == {"revenue_paise", "rewards_paise", "attempts", "signups"}
    assert body["active_learners_7d"] == 0
    assert body["top_courses"] == []
    assert body["top_learners"] == []
    assert body["recent_attempts"] == []


def test_other_users_cannot_reach_the_quiz_answers(client, db, auth_headers):
    """A learner's quiz payload has no `correct_index`, even with a subscription."""
    from test_attempts import _seed_quiz, _subscribe

    task = _seed_quiz(db)
    headers = auth_headers()
    _subscribe(db)
    response = client.get(f"{API}/tasks/{task.id}/quiz", headers=headers)
    assert response.status_code == 200
    payload = response.json()["questions"]
    assert all("correct_index" not in question for question in payload)


def test_task_config_stays_server_side(client, db, auth_headers):
    from test_attempts import _seed_quiz, _subscribe

    task = _seed_quiz(db)
    headers = auth_headers()
    _subscribe(db)
    response = client.get(f"{API}/tasks/{task.id}", headers=headers)
    assert response.status_code == 200
    assert "config" not in response.json()

    stored = db.get(Task, task.id)
    assert stored.config["questions"][0]["correct_index"] == 1
