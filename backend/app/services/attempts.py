"""The submission flow: limits, grading, recording and reward payout.

Kept separate from the router so the rules can be unit-tested without HTTP, and
so the router stays a thin translation layer.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Attempt, Task, User
from ..utils import utcnow
from .grading import GradingError, grade_quiz_submission
from .rewards import RewardOutcome, grant_reward
from .settings_store import RuntimeSettings


class SubmissionError(Exception):
    """A submission that cannot be accepted. `status_code` maps to HTTP."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class SubmissionResult:
    attempt_id: int
    created_at: datetime
    percent: int
    passed: bool
    correct_count: int
    question_count: int
    reward: RewardOutcome


def _latest_attempt_at(db: Session, user_id: int, task_id: int):
    return db.scalar(
        select(func.max(Attempt.created_at)).where(
            Attempt.user_id == user_id, Attempt.task_id == task_id
        )
    )


def _enforce_limits(db: Session, *, user_id: int, task_id: int, settings: RuntimeSettings) -> None:
    """Cooldown between attempts on one task, plus a per-user rate limit."""
    if settings.attempt_cooldown_seconds > 0:
        last = _latest_attempt_at(db, user_id, task_id)
        if last is not None:
            elapsed = (utcnow() - last).total_seconds()
            if elapsed < settings.attempt_cooldown_seconds:
                wait = max(1, int(settings.attempt_cooldown_seconds - elapsed))
                raise SubmissionError(
                    f"Please wait {wait} more second(s) before trying this task again.", 429
                )

    if settings.submission_rate_limit_per_minute > 0:
        since = utcnow() - timedelta(minutes=1)
        recent = db.scalar(
            select(func.count(Attempt.id)).where(
                Attempt.user_id == user_id, Attempt.created_at >= since
            )
        )
        if (recent or 0) >= settings.submission_rate_limit_per_minute:
            raise SubmissionError(
                "You are submitting too quickly. Please try again in a minute.", 429
            )


def submit_quiz(
    db: Session,
    *,
    user: User,
    task: Task,
    answers: dict[str, int],
    settings: RuntimeSettings,
) -> SubmissionResult:
    """Grade, record and (when it passes) pay a quiz attempt."""
    if not task.is_active:
        raise SubmissionError("That task is no longer available.", 404)

    _enforce_limits(db, user_id=user.id, task_id=task.id, settings=settings)

    try:
        outcome = grade_quiz_submission(task, answers)
    except GradingError as exc:
        raise SubmissionError(str(exc), 422) from exc

    attempt = Attempt(
        user_id=user.id,
        task_id=task.id,
        percent=outcome.percent,
        passed=outcome.passed,
    )
    db.add(attempt)
    db.flush()

    reward = RewardOutcome(False, 0, "not_passed", task.reward)
    if outcome.passed:
        # The attempt row and the reward row are committed together.
        reward = grant_reward(db, user_id=user.id, task=task, settings=settings)

    db.commit()
    db.refresh(attempt)

    return SubmissionResult(
        attempt_id=attempt.id,
        created_at=attempt.created_at,
        percent=outcome.percent,
        passed=outcome.passed,
        correct_count=outcome.correct_count,
        question_count=outcome.question_count,
        reward=reward,
    )


def list_attempts(
    db: Session, user_id: int, *, limit: int = 20, offset: int = 0
) -> tuple[list[tuple[Attempt, str]], int]:
    """A learner's own attempts, newest first, with the task title attached."""
    rows = db.execute(
        select(Attempt, Task.title)
        .join(Task, Attempt.task_id == Task.id)
        .where(Attempt.user_id == user_id)
        .order_by(Attempt.created_at.desc(), Attempt.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    total = int(
        db.scalar(select(func.count(Attempt.id)).where(Attempt.user_id == user_id)) or 0
    )
    return [(row[0], row[1]) for row in rows], total
