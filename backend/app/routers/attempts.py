"""Assessments: fetch the questions, submit answers, review your own attempts.

Every route here needs access, because the questions *are* the thing being paid
for: a free course needs an active subscription, and a paid course needs the
purchase that unlocks it. Grading and the reward decision happen in
`services.attempts` - this module only translates HTTP to that.
"""

from fastapi import APIRouter, HTTPException, Query, status

from ..deps import CurrentUser, DbSession
from ..schemas import (
    AttemptOut,
    AttemptResultOut,
    AttemptSubmitRequest,
    ErrorResponse,
    Page,
    QuizOut,
)
from ..services import attempts as attempts_service
from ..services import catalog
from ..services import progress as progress_service
from ..services import purchases
from ..services.attempts import SubmissionError
from ..services.progress import ProgressError
from ..services.purchases import PurchaseError
from ..services.rewards import (
    ALREADY_REWARDED,
    DAILY_LIMIT_REACHED,
    LIMIT_CAPPED,
    REWARDS_DISABLED,
)
from ..services.settings_store import runtime_settings
from ..utils import format_paise
from ..models import TaskType

router = APIRouter(tags=["assessment"])


def _load_active_task(db, task_id: int):
    task = catalog.get_task(db, task_id)
    if task is None or not task.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That task is no longer available.",
        )
    return task


def _assert_access(db, user, task) -> None:
    """A paid course must be bought; a free one needs an active subscription."""
    try:
        purchases.assert_task_access(db, user, task)
    except PurchaseError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


def _assert_topic_ready(db, user, task) -> None:
    """The video has to be watched and understood before an assessment opens.

    Enforced here rather than in the browser, so posting answers directly is
    refused just as firmly as clicking a locked button.
    """
    try:
        progress_service.assert_topic_ready(db, user=user, topic=task.topic)
    except ProgressError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


def _reward_message(result: attempts_service.SubmissionResult, pass_percent: int) -> str:
    reward = result.reward

    if not result.passed:
        return (
            f"You scored {result.percent}% and needed {pass_percent}% to pass. "
            "Review the material and try again."
        )

    if reward.granted and reward.reason == LIMIT_CAPPED:
        return (
            f"Passed with {result.percent}%. A capped reward of "
            f"{format_paise(reward.amount_paise)} was added to your wallet."
        )
    if reward.granted:
        return (
            f"Passed with {result.percent}%. {format_paise(reward.amount_paise)} "
            "was added to your wallet."
        )

    reasons = {
        ALREADY_REWARDED: "You had already earned the reward for this task, so it was paid once only.",
        REWARDS_DISABLED: "Rewards are paused across the platform right now, so none was paid.",
        DAILY_LIMIT_REACHED: (
            "You have reached today's reward limit. The task stays passed; "
            "no reward was added today."
        ),
    }
    tail = reasons.get(reward.reason, "No reward was added for this attempt.")
    return f"Passed with {result.percent}%. {tail}"


@router.get(
    "/tasks/{task_id}/quiz",
    response_model=QuizOut,
    summary="The quiz questions (answers are never sent to the browser)",
    responses={
        402: {"model": ErrorResponse, "description": "Subscription or course purchase required"},
        403: {"model": ErrorResponse, "description": "Video or understanding check not done"},
        404: {"model": ErrorResponse, "description": "No such task"},
    },
)
def read_quiz(task_id: int, db: DbSession, user: CurrentUser) -> QuizOut:
    task = _load_active_task(db, task_id)
    if task.type != TaskType.quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That task is not a quiz.",
        )
    _assert_access(db, user, task)
    _assert_topic_ready(db, user, task)
    return catalog.to_quiz_public(task)


@router.post(
    "/tasks/{task_id}/attempts",
    response_model=AttemptResultOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit answers; the server grades them and decides the reward",
    responses={
        402: {"model": ErrorResponse, "description": "Subscription or course purchase required"},
        403: {"model": ErrorResponse, "description": "Video or understanding check not done"},
        404: {"model": ErrorResponse, "description": "No such task"},
        429: {"model": ErrorResponse, "description": "Too many submissions"},
    },
)
def submit_attempt(
    task_id: int,
    payload: AttemptSubmitRequest,
    db: DbSession,
    user: CurrentUser,
) -> AttemptResultOut:
    task = _load_active_task(db, task_id)
    _assert_access(db, user, task)
    _assert_topic_ready(db, user, task)

    try:
        result = attempts_service.submit_quiz(
            db,
            user=user,
            task=task,
            answers=payload.answers,
            settings=runtime_settings(db),
        )
    except SubmissionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return AttemptResultOut(
        attempt=AttemptOut(
            id=result.attempt_id,
            task_id=task.id,
            task_title=task.title,
            percent=result.percent,
            passed=result.passed,
            created_at=result.created_at,
        ),
        percent=result.percent,
        passed=result.passed,
        correct_count=result.correct_count,
        question_count=result.question_count,
        reward_paise=result.reward.amount_paise,
        reward_granted=result.reward.granted,
        reward_reason=result.reward.reason,
        message=_reward_message(result, task.pass_percent),
    )


@router.get(
    "/me/attempts",
    response_model=Page[AttemptOut],
    summary="Your own attempt history, newest first",
)
def read_my_attempts(
    db: DbSession,
    user: CurrentUser,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Page[AttemptOut]:
    rows, total = attempts_service.list_attempts(db, user.id, limit=limit, offset=offset)
    return Page[AttemptOut](
        items=[
            AttemptOut(
                id=attempt.id,
                task_id=attempt.task_id,
                task_title=task_title,
                percent=attempt.percent,
                passed=attempt.passed,
                created_at=attempt.created_at,
            )
            for attempt, task_title in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )
