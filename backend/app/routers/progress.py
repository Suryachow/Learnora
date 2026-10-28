"""Video completion and the understanding check.

Both routes are free for a free course - that material is not what people pay
for. A paid course is refused until it is bought, so no progress (and no lesson
reward) can be recorded against material the learner cannot open. The assessment
routes read the same records, which is what makes the sequence
video -> understanding -> quiz a rule rather than a suggestion.
"""

from fastapi import APIRouter, HTTPException, status

from ..deps import CurrentUser, DbSession
from ..schemas import (
    ErrorResponse,
    ProgressSummaryOut,
    TopicProgressOut,
    UnderstandingRequest,
    VideoCompleteRequest,
)
from ..services import catalog, progress as progress_service, purchases
from ..services.progress import ProgressError
from ..services.purchases import PurchaseError
from ..services.settings_store import runtime_settings

router = APIRouter(tags=["progress"])

_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="We could not find that lesson in the Learnora catalogue.",
)


def _load_topic(db, topic_id: int):
    topic = catalog.get_topic(db, topic_id)
    if topic is None:
        raise _NOT_FOUND
    return topic


def _raise(exc: ProgressError | PurchaseError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


def _assert_access(db, user, topic) -> None:
    """A paid course withholds its lessons until the purchase is made."""
    try:
        purchases.require_access(db, user, topic.course)
    except PurchaseError as exc:
        _raise(exc)


@router.post(
    "/topics/{topic_id}/video-complete",
    response_model=TopicProgressOut,
    summary="Record that the lesson video was watched to the end",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "No such topic"},
        409: {"model": ErrorResponse, "description": "The topic has no trackable video"},
        422: {"model": ErrorResponse, "description": "The video was not watched in full"},
    },
)
def complete_video(
    topic_id: int,
    payload: VideoCompleteRequest,
    db: DbSession,
    user: CurrentUser,
) -> TopicProgressOut:
    topic = _load_topic(db, topic_id)
    _assert_access(db, user, topic)
    try:
        return progress_service.record_video_complete(
            db,
            user=user,
            topic=topic,
            watched_seconds=payload.watched_seconds,
            duration_seconds=payload.duration_seconds,
            settings=runtime_settings(db),
        )
    except ProgressError as exc:
        _raise(exc)


@router.post(
    "/topics/{topic_id}/understanding",
    response_model=TopicProgressOut,
    summary="How well the video was understood (answered after watching it)",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "No such topic"},
        409: {"model": ErrorResponse, "description": "The video is not complete yet"},
    },
)
def save_understanding(
    topic_id: int,
    payload: UnderstandingRequest,
    db: DbSession,
    user: CurrentUser,
) -> TopicProgressOut:
    topic = _load_topic(db, topic_id)
    _assert_access(db, user, topic)
    try:
        return progress_service.record_understanding(
            db,
            user=user,
            topic=topic,
            rating=payload.rating.value,
            note=payload.note,
        )
    except ProgressError as exc:
        _raise(exc)


@router.get(
    "/me/progress",
    response_model=ProgressSummaryOut,
    summary="How much of the video catalogue you have worked through",
)
def read_my_progress(db: DbSession, user: CurrentUser) -> ProgressSummaryOut:
    counts = progress_service.summarise(db, user.id)
    return ProgressSummaryOut(
        videos_completed=counts["videos_completed"],
        videos_available=catalog.count_topics_with_video(db),
        understanding_recorded=counts["understanding_recorded"],
    )
