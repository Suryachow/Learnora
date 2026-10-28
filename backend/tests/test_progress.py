"""The lesson path: watch the video to the end, say how it went, then assess.

The point of these tests is that the sequence is a *server* rule. Posting to the
assessment endpoints directly must be refused exactly like clicking a locked
button, and a lesson cannot be marked complete after a few seconds of playback.
"""

from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import Course, Task, TaskType, Topic, Transaction, TransactionKind, User
from app.services.settings_store import update_settings
from app.utils import utcnow

from conftest import API

VIDEO = "https://www.youtube.com/embed/dQw4w9WgXcQ"


def _seed_topic(db, *, video_url: str | None = VIDEO, published: bool = True) -> tuple[Topic, Task]:
    """A published lesson with a quiz, optionally carrying a trackable video."""
    course = Course(title="Python", category="Python", description="", is_published=published)
    db.add(course)
    db.flush()
    topic = Topic(
        course_id=course.id, title="Basics", content="", position=0, video_url=video_url
    )
    db.add(topic)
    db.flush()
    task = Task(
        topic_id=topic.id,
        title="Basics check",
        type=TaskType.quiz,
        pass_percent=60,
        reward=2000,
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
    db.refresh(topic)
    db.refresh(task)
    return topic, task


def _subscribe(db, email: str = "learner@example.com") -> User:
    user = db.scalar(select(User).where(User.email == email))
    user.subscribed_until = utcnow() + timedelta(days=30)
    db.commit()
    db.refresh(user)
    return user


def _watch(client, topic, headers, *, watched=600, duration=600):
    return client.post(
        f"{API}/topics/{topic.id}/video-complete",
        json={"watched_seconds": watched, "duration_seconds": duration},
        headers=headers,
    )


def _understand(client, topic, headers, *, rating="confident", note=""):
    return client.post(
        f"{API}/topics/{topic.id}/understanding",
        json={"rating": rating, "note": note},
        headers=headers,
    )


@pytest.fixture(autouse=True)
def _no_limits(db):
    update_settings(
        db,
        {"attempt_cooldown_seconds": 0, "submission_rate_limit_per_minute": 600},
        updated_by=None,
    )


# ---------------------------------------------------------------------------
# Recording the watch
# ---------------------------------------------------------------------------


def test_partial_watch_is_refused(client, db, auth_headers):
    topic, _ = _seed_topic(db)
    headers = auth_headers()

    response = _watch(client, topic, headers, watched=90, duration=600)

    assert response.status_code == 422
    assert "not been watched in full" in response.json()["detail"]


def test_full_watch_marks_the_video_complete(client, db, auth_headers):
    topic, _ = _seed_topic(db)
    headers = auth_headers()

    response = _watch(client, topic, headers)

    assert response.status_code == 200
    body = response.json()
    assert body["video_completed_at"] is not None
    assert body["video_watched_seconds"] == 600
    assert body["understood_at"] is None


def test_replaying_a_lesson_keeps_the_first_completion(client, db, auth_headers):
    topic, _ = _seed_topic(db)
    headers = auth_headers()

    first = client.post(
        f"{API}/topics/{topic.id}/video-complete",
        json={"watched_seconds": 600, "duration_seconds": 600},
        headers=headers,
    ).json()

    again = client.post(
        f"{API}/topics/{topic.id}/video-complete",
        json={"watched_seconds": 900, "duration_seconds": 900},
        headers=headers,
    ).json()

    assert again["video_completed_at"] == first["video_completed_at"]
    assert again["video_duration_seconds"] == 900


def test_a_lesson_without_a_trackable_video_cannot_be_completed(client, db, auth_headers):
    topic, _ = _seed_topic(db, video_url=None)
    headers = auth_headers()

    response = _watch(client, topic, headers)

    assert response.status_code == 409
    assert "no trackable video" in response.json()["detail"]


def test_video_completion_needs_a_signed_in_learner(client, db):
    topic, _ = _seed_topic(db)

    response = client.post(
        f"{API}/topics/{topic.id}/video-complete",
        json={"watched_seconds": 600, "duration_seconds": 600},
    )

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# The understanding check
# ---------------------------------------------------------------------------


def test_understanding_is_refused_before_the_video_is_watched(client, db, auth_headers):
    topic, _ = _seed_topic(db)
    headers = auth_headers()

    response = _understand(client, topic, headers)

    assert response.status_code == 409
    assert "Finish the video" in response.json()["detail"]


def test_understanding_is_stored_after_the_video(client, db, auth_headers):
    topic, _ = _seed_topic(db)
    headers = auth_headers()
    _watch(client, topic, headers)

    response = _understand(client, topic, headers, rating="mostly", note="  rewatched part 2  ")

    assert response.status_code == 200
    body = response.json()
    assert body["understanding"] == "mostly"
    assert body["understanding_note"] == "rewatched part 2"
    assert body["understood_at"] is not None


def test_understanding_rejects_an_unknown_rating(client, db, auth_headers):
    topic, _ = _seed_topic(db)
    headers = auth_headers()
    _watch(client, topic, headers)

    response = _understand(client, topic, headers, rating="brilliant")

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# The assessment gate
# ---------------------------------------------------------------------------


def test_quiz_stays_locked_until_the_lesson_is_done(client, db, auth_headers):
    topic, task = _seed_topic(db)
    headers = auth_headers()
    _subscribe(db)

    locked = client.get(f"{API}/tasks/{task.id}/quiz", headers=headers)
    assert locked.status_code == 403
    assert "Watch the video" in locked.json()["detail"]

    _watch(client, topic, headers)
    needs_understanding = client.get(f"{API}/tasks/{task.id}/quiz", headers=headers)
    assert needs_understanding.status_code == 403
    assert "understood the video" in needs_understanding.json()["detail"]

    _understand(client, topic, headers)
    opened = client.get(f"{API}/tasks/{task.id}/quiz", headers=headers)
    assert opened.status_code == 200
    for question in opened.json()["questions"]:
        assert "correct_index" not in question


def test_posting_answers_directly_is_refused_until_the_lesson_is_done(client, db, auth_headers):
    topic, task = _seed_topic(db)
    headers = auth_headers()
    _subscribe(db)

    blocked = client.post(
        f"{API}/tasks/{task.id}/attempts",
        json={"answers": {"q1": 1, "q2": 1}},
        headers=headers,
    )
    assert blocked.status_code == 403

    _watch(client, topic, headers)
    _understand(client, topic, headers)

    graded = client.post(
        f"{API}/tasks/{task.id}/attempts",
        json={"answers": {"q1": 1, "q2": 1}},
        headers=headers,
    )
    assert graded.status_code == 201, graded.text
    assert graded.json()["passed"] is True


def test_the_gate_is_skipped_when_the_lesson_has_no_trackable_video(client, db, auth_headers):
    _, task = _seed_topic(db, video_url=None)
    headers = auth_headers()
    _subscribe(db)

    response = client.get(f"{API}/tasks/{task.id}/quiz", headers=headers)

    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Reading the progress back
# ---------------------------------------------------------------------------


def test_topic_detail_shows_progress_only_to_the_signed_in_reader(client, db, auth_headers):
    topic, _ = _seed_topic(db)
    headers = auth_headers()
    _watch(client, topic, headers)

    guest = client.get(f"{API}/topics/{topic.id}")
    assert guest.status_code == 200
    assert guest.json()["progress"] is None

    mine = client.get(f"{API}/topics/{topic.id}", headers=headers)
    assert mine.status_code == 200
    assert mine.json()["progress"]["video_completed_at"] is not None


def test_progress_summary_counts_lessons_with_videos(client, db, auth_headers):
    topic, _ = _seed_topic(db)
    headers = auth_headers()

    empty = client.get(f"{API}/me/progress", headers=headers).json()
    assert empty == {"videos_completed": 0, "videos_available": 1, "understanding_recorded": 0}

    _watch(client, topic, headers)
    _understand(client, topic, headers)

    worked = client.get(f"{API}/me/progress", headers=headers).json()
    assert worked["videos_completed"] == 1
    assert worked["videos_available"] == 1
    assert worked["understanding_recorded"] == 1


# ---------------------------------------------------------------------------
# Admin reporting
# ---------------------------------------------------------------------------


def test_admin_report_includes_video_and_understanding_totals(
    client, db, auth_headers, make_admin, login
):
    topic, _ = _seed_topic(db)
    headers = auth_headers()
    _watch(client, topic, headers)
    _understand(client, topic, headers, rating="confident")

    make_admin(email="boss@example.com")
    token = login(email="boss@example.com")

    response = client.get(
        f"{API}/admin/reports/overview", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["video_completions"] == 1
    counts = {row["rating"]: row["count"] for row in body["understanding_counts"]}
    assert set(counts) == {"not_yet", "mostly", "confident"}
    assert counts["confident"] == 1
    assert counts["mostly"] == 0


def test_progress_is_scoped_to_the_learner_who_watched(client, db, auth_headers):
    topic, task = _seed_topic(db)
    watcher = auth_headers(email="watcher@example.com")
    _watch(client, topic, watcher)

    other = auth_headers(email="other@example.com")
    summary = client.get(f"{API}/me/progress", headers=other).json()

    assert summary["videos_completed"] == 0
    assert client.get(f"{API}/topics/{topic.id}", headers=other).json()["progress"] is None


# ---------------------------------------------------------------------------
# The lesson reward
# ---------------------------------------------------------------------------


def test_finishing_a_video_pays_the_lesson_reward_once(client, db, auth_headers):
    topic, _ = _seed_topic(db)
    headers = auth_headers()

    first = _watch(client, topic, headers)
    assert first.status_code == 200
    body = first.json()
    assert body["reward_granted"] is True
    assert body["reward_paise"] == 500
    assert body["reward_reason"] == "granted"

    again = _watch(client, topic, headers).json()
    assert again["reward_granted"] is False
    assert again["reward_reason"] == "already_rewarded"

    wallet = client.get(f"{API}/wallet", headers=headers).json()
    assert wallet["balance_paise"] == 500
    assert wallet["lifetime_earned_paise"] == 500
    assert wallet["transactions"]["total"] == 1


def test_the_lesson_reward_row_names_the_topic(client, db, auth_headers):
    topic, _ = _seed_topic(db)
    _watch(client, topic, auth_headers())

    row = db.scalar(select(Transaction).where(Transaction.topic_id == topic.id))

    assert row is not None
    assert row.kind == TransactionKind.reward
    assert row.task_id is None
    assert row.amount == 500


def test_the_global_switch_stops_lesson_rewards(client, db, auth_headers):
    topic, _ = _seed_topic(db)
    update_settings(db, {"rewards_enabled": False}, updated_by=None)
    headers = auth_headers()

    body = _watch(client, topic, headers).json()

    assert body["reward_granted"] is False
    assert body["reward_reason"] == "rewards_disabled"
    assert client.get(f"{API}/wallet", headers=headers).json()["balance_paise"] == 0


def test_the_daily_limit_caps_the_lesson_reward(client, db, auth_headers):
    topic, _ = _seed_topic(db)
    update_settings(db, {"reward_daily_limit_paise": 200}, updated_by=None)
    headers = auth_headers()

    body = _watch(client, topic, headers).json()

    assert body["reward_granted"] is True
    assert body["reward_paise"] == 200
    assert body["reward_reason"] == "limit_capped"


def test_a_zero_lesson_reward_pays_nothing(client, db, auth_headers):
    topic, _ = _seed_topic(db)
    update_settings(db, {"video_reward_paise": 0}, updated_by=None)
    headers = auth_headers()

    body = _watch(client, topic, headers).json()

    assert body["reward_granted"] is False
    assert body["reward_reason"] == "nothing_to_pay"
    assert client.get(f"{API}/wallet", headers=headers).json()["balance_paise"] == 0
