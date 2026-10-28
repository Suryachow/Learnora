"""Video completion and the understanding check.

Design notes:

* The video is a YouTube iframe, so playback cannot be verified by the server.
  The browser reports what it watched and the server refuses anything that does
  not cover almost the whole runtime - a client cannot mark a lesson complete
  after a few seconds.
* The understanding rating is only accepted after the video is complete, so the
  sequence video -> understanding -> assessment holds on the server too.
* Both calls are idempotent: the first completion timestamp is kept, so
  re-watching a lesson never resets progress.
* The lesson reward is paid by the same commit that records the completion, so
  a learner can never be credited without the progress row (or the reverse).
"""

import math
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import TopicProgress, User
from ..models.topic import Topic
from ..schemas.progress import TopicProgressOut
from ..utils import utcnow
from .rewards import RewardOutcome, grant_video_reward
from .settings_store import RuntimeSettings

#: How much of the runtime must have actually played before completion counts.
WATCHED_RATIO = 0.9
#: Reported watch time is allowed to fall this far short of the runtime, which
#: absorbs buffering and the last sampling tick.
GRACE_SECONDS = 3


class ProgressError(Exception):
    def __init__(self, message: str, status_code: int = 422) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def is_trackable_video(url: str | None) -> bool:
    """Only YouTube lessons can be tracked, because only they expose the player API."""
    if not url:
        return False
    return "youtube.com" in url or "youtu.be" in url


def is_gated(topic: Topic) -> bool:
    """Topics with a trackable video must be watched and understood first."""
    return is_trackable_video(topic.video_url)


def _minimum_watched(duration_seconds: int) -> int:
    """The watch time that counts as "the whole video", allowing for the last tick."""
    return max(0, math.ceil(duration_seconds * WATCHED_RATIO) - GRACE_SECONDS)


def progress_out(
    progress: TopicProgress | None,
    topic_id: int,
    reward: RewardOutcome | None = None,
) -> TopicProgressOut | None:
    if progress is None:
        return None
    return TopicProgressOut(
        topic_id=topic_id,
        video_completed_at=progress.video_completed_at,
        video_watched_seconds=progress.video_watched_seconds,
        video_duration_seconds=progress.video_duration_seconds,
        understanding=progress.understanding,
        understanding_note=progress.understanding_note,
        understood_at=progress.understood_at,
        reward_granted=bool(reward and reward.granted),
        reward_paise=reward.amount_paise if reward else 0,
        reward_reason=reward.reason if reward else "",
    )


def get(db: Session, user_id: int, topic_id: int) -> TopicProgress | None:
    return db.scalars(
        select(TopicProgress).where(
            TopicProgress.user_id == user_id, TopicProgress.topic_id == topic_id
        )
    ).first()


def _get_or_create(db: Session, user_id: int, topic_id: int) -> TopicProgress:
    progress = get(db, user_id, topic_id)
    if progress is None:
        progress = TopicProgress(user_id=user_id, topic_id=topic_id)
        db.add(progress)
    return progress


def record_video_complete(
    db: Session,
    *,
    user: User,
    topic: Topic,
    watched_seconds: int,
    duration_seconds: int,
    settings: RuntimeSettings,
) -> TopicProgressOut:
    if not is_trackable_video(topic.video_url):
        raise ProgressError("This topic has no trackable video to complete.", status_code=409)

    minimum = _minimum_watched(duration_seconds)
    if watched_seconds < minimum:
        remaining = max(0, duration_seconds - watched_seconds)
        raise ProgressError(
            "The video has not been watched in full - about "
            f"{remaining // 60}m {remaining % 60}s of it is still unwatched."
        )

    progress = _get_or_create(db, user.id, topic.id)
    first_completion = progress.video_completed_at is None
    # Keep the first completion time: re-watching must not move it.
    if first_completion:
        progress.video_completed_at = utcnow()
    # Column defaults only land on flush, so an unsaved row reads back as None.
    progress.video_watched_seconds = max(progress.video_watched_seconds or 0, watched_seconds)
    progress.video_duration_seconds = max(progress.video_duration_seconds or 0, duration_seconds)

    # Idempotent like the completion itself: the ledger row is written only on
    # the first finish, and a repeat call reports that it was already paid.
    reward = grant_video_reward(db, user_id=user.id, topic=topic, settings=settings)

    db.commit()
    db.refresh(progress)
    return progress_out(progress, topic.id, reward)


def record_understanding(
    db: Session,
    *,
    user: User,
    topic: Topic,
    rating: str,
    note: str,
) -> TopicProgressOut:
    progress = get(db, user.id, topic.id)
    if progress is None or progress.video_completed_at is None:
        raise ProgressError(
            "Finish the video for this topic before answering the understanding check.",
            status_code=409,
        )

    progress.understanding = rating
    progress.understanding_note = note
    if progress.understood_at is None:
        progress.understood_at = utcnow()

    db.commit()
    db.refresh(progress)
    return progress_out(progress, topic.id)


def assert_topic_ready(db: Session, *, user: User, topic: Topic) -> None:
    """The gate the assessment routes call: video watched, then understanding given."""
    if not is_gated(topic):
        return

    progress = get(db, user.id, topic.id)
    if progress is None or progress.video_completed_at is None:
        raise ProgressError(
            "Watch the video in this topic all the way to the end before starting the assessment.",
            status_code=403,
        )
    if progress.understood_at is None:
        raise ProgressError(
            "Tell us how well you understood the video before starting the assessment.",
            status_code=403,
        )


def summarise(db: Session, user_id: int) -> dict[str, int]:
    """Counts for the dashboard: how much of the catalogue has been worked through."""
    rows = db.scalars(select(TopicProgress).where(TopicProgress.user_id == user_id)).all()
    return {
        "videos_completed": sum(1 for row in rows if row.video_completed_at is not None),
        "understanding_recorded": sum(1 for row in rows if row.understood_at is not None),
    }


def last_activity(progress: TopicProgress) -> datetime | None:
    return progress.understood_at or progress.video_completed_at
