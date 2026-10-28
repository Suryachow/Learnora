"""Public catalogue: courses, topics and the answer-free view of a task.

Courses and topics are readable without an account so people can see what they
are buying. Task detail needs a signed-in user, and never exposes `config`.
"""

from fastapi import APIRouter, HTTPException, Query, status

from ..deps import CurrentUser, DbSession, OptionalUser
from ..schemas import (
    CategorySummary,
    CourseDetail,
    CourseSummary,
    ErrorResponse,
    TaskPublic,
    TopicDetail,
)
from ..services import catalog
from ..services import progress as progress_service
from ..services import purchases

router = APIRouter(tags=["learning"])

_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="We could not find that page in the Learnora catalogue.",
)


@router.get(
    "/categories",
    response_model=list[CategorySummary],
    summary="List course categories with how many courses each has",
)
def read_categories(db: DbSession) -> list[CategorySummary]:
    return catalog.list_categories(db)


@router.get(
    "/courses",
    response_model=list[CourseSummary],
    summary="Browse published courses",
)
def read_courses(
    db: DbSession,
    category: str | None = Query(default=None, max_length=100, description="Filter by category"),
    search: str | None = Query(default=None, max_length=100, description="Match title or text"),
) -> list[CourseSummary]:
    return catalog.list_courses(db, category=category, search=search)


@router.get(
    "/courses/{course_id}",
    response_model=CourseDetail,
    summary="One course with its topics",
    responses={404: {"model": ErrorResponse, "description": "No such course"}},
)
def read_course(course_id: int, db: DbSession, user: OptionalUser) -> CourseDetail:
    course = catalog.get_course(db, course_id)
    if course is None:
        raise _NOT_FOUND

    # A paid course hides nothing about itself - only whether this reader owns it.
    access, expires_at = purchases.viewer_access(db, user, course)
    return catalog.to_course_detail(course, has_access=access, access_expires_at=expires_at)


@router.get(
    "/topics/{topic_id}",
    response_model=TopicDetail,
    summary="Learning material, video and the tasks inside a topic",
    responses={404: {"model": ErrorResponse, "description": "No such topic"}},
)
def read_topic(topic_id: int, db: DbSession, user: OptionalUser) -> TopicDetail:
    topic = catalog.get_topic(db, topic_id)
    if topic is None:
        raise _NOT_FOUND

    # Anyone can read a free lesson; a paid one opens after the purchase. A
    # signed-in reader with access also sees their own progress.
    access, _ = purchases.viewer_access(db, user, topic.course)
    progress = progress_service.get(db, user.id, topic.id) if user and access else None
    return catalog.to_topic_detail(topic, progress, has_access=access)


@router.get(
    "/tasks/{task_id}",
    response_model=TaskPublic,
    summary="Task summary (never includes the answers)",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "No such task"},
    },
)
def read_task(task_id: int, db: DbSession, _user: CurrentUser) -> TaskPublic:
    task = catalog.get_task(db, task_id)
    if task is None or not task.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That task is no longer available.",
        )
    return catalog.to_task_public(task)
