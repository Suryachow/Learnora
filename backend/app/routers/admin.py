"""The admin console API. Every route here is behind `AdminUser`.

Organised as: catalogue CRUD, task/quiz builder, user management, reports and
the runtime settings screen. Admin payloads may include quiz answers, because
an admin is who authors them.
"""

from fastapi import APIRouter, HTTPException, Query, status

from ..deps import AdminUser, DbSession
from ..models import Course, Task, TaskType, Topic, User
from ..schemas import (
    AdminUserOut,
    AdminUserUpdate,
    CourseAdminOut,
    CourseUpdate,
    CourseWrite,
    ErrorResponse,
    Page,
    ReportOverview,
    SettingOut,
    SettingsUpdateRequest,
    TaskAdminDetail,
    TaskAdminOut,
    TaskUpdate,
    TaskWrite,
    TopicAdminOut,
    TopicReorderRequest,
    TopicUpdate,
    TopicWrite,
)
from ..services import admin as admin_service
from ..services.settings_store import (
    SettingError,
    describe,
    reset_setting,
    runtime_settings,
    update_settings,
)
from ..services.subscription import activate_subscription
from ..utils import utcnow

router = APIRouter(prefix="/admin", tags=["admin"])

_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="That record no longer exists.",
)


def _get_course(db: DbSession, course_id: int) -> Course:
    course = admin_service.get_course_full(db, course_id)
    if course is None:
        raise _NOT_FOUND
    return course


def _get_topic(db: DbSession, topic_id: int) -> Topic:
    topic = admin_service.get_topic_full(db, topic_id)
    if topic is None:
        raise _NOT_FOUND
    return topic


def _get_task(db: DbSession, task_id: int) -> Task:
    task = admin_service.get_task_full(db, task_id)
    if task is None:
        raise _NOT_FOUND
    return task


# ---------------------------------------------------------------------------
# Catalogue - courses
# ---------------------------------------------------------------------------


@router.get(
    "/courses",
    response_model=list[CourseAdminOut],
    summary="Every course, published or not",
)
def list_courses(
    db: DbSession,
    _admin: AdminUser,
    search: str | None = Query(default=None, max_length=100),
) -> list[CourseAdminOut]:
    return [CourseAdminOut(**row) for row in admin_service.list_courses_admin(db, search=search)]


@router.post(
    "/courses",
    response_model=CourseAdminOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a course",
)
def create_course(payload: CourseWrite, db: DbSession, _admin: AdminUser) -> CourseAdminOut:
    course = Course(
        title=payload.title,
        category=payload.category,
        description=payload.description,
        is_published=payload.is_published,
        price_paise=payload.price_paise,
        cover_image_url=payload.cover_image_url,
        level=payload.level,
        duration_minutes=payload.duration_minutes,
        outcomes=payload.outcomes,
        access_days=payload.access_days,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return CourseAdminOut(**admin_service.course_admin_out(_get_course(db, course.id)))


@router.patch(
    "/courses/{course_id}",
    response_model=CourseAdminOut,
    summary="Update a course",
    responses={404: {"model": ErrorResponse, "description": "No such course"}},
)
def update_course(
    course_id: int, payload: CourseUpdate, db: DbSession, _admin: AdminUser
) -> CourseAdminOut:
    course = _get_course(db, course_id)
    # Only the fields the console sent; an explicit null clears an optional one.
    for field, value in payload.changes().items():
        setattr(course, field, value)
    db.add(course)
    db.commit()
    buyers = admin_service.purchase_count(db, course_id)
    return CourseAdminOut(**admin_service.course_admin_out(_get_course(db, course_id), buyers))


@router.delete(
    "/courses/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a course, its topics and their tasks",
    responses={404: {"model": ErrorResponse, "description": "No such course"}},
)
def delete_course(course_id: int, db: DbSession, _admin: AdminUser) -> None:
    course = _get_course(db, course_id)
    db.delete(course)
    db.commit()


# ---------------------------------------------------------------------------
# Catalogue - topics
# ---------------------------------------------------------------------------


@router.get(
    "/courses/{course_id}/topics",
    response_model=list[TopicAdminOut],
    summary="The topics inside one course, in order",
    responses={404: {"model": ErrorResponse, "description": "No such course"}},
)
def list_topics(course_id: int, db: DbSession, _admin: AdminUser) -> list[TopicAdminOut]:
    _get_course(db, course_id)
    return [TopicAdminOut(**row) for row in admin_service.list_topics_admin(db, course_id)]


@router.post(
    "/courses/{course_id}/topics",
    response_model=TopicAdminOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a topic to a course",
    responses={404: {"model": ErrorResponse, "description": "No such course"}},
)
def create_topic(
    course_id: int, payload: TopicWrite, db: DbSession, _admin: AdminUser
) -> TopicAdminOut:
    _get_course(db, course_id)
    position = payload.position or admin_service.next_topic_position(db, course_id)
    topic = Topic(
        course_id=course_id,
        title=payload.title.strip(),
        content=payload.content,
        video_url=payload.video_url or None,
        position=position,
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return TopicAdminOut(**admin_service.topic_admin_out(_get_topic(db, topic.id)))


@router.patch(
    "/topics/{topic_id}",
    response_model=TopicAdminOut,
    summary="Update a topic",
    responses={404: {"model": ErrorResponse, "description": "No such topic"}},
)
def update_topic(
    topic_id: int, payload: TopicUpdate, db: DbSession, _admin: AdminUser
) -> TopicAdminOut:
    topic = _get_topic(db, topic_id)
    changes = payload.model_dump(exclude_none=True)
    if "title" in changes:
        changes["title"] = changes["title"].strip()
    if "video_url" in changes and not changes["video_url"]:
        changes["video_url"] = None
    for field, value in changes.items():
        setattr(topic, field, value)
    db.add(topic)
    db.commit()
    return TopicAdminOut(**admin_service.topic_admin_out(_get_topic(db, topic_id)))


@router.delete(
    "/topics/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a topic and its tasks",
    responses={404: {"model": ErrorResponse, "description": "No such topic"}},
)
def delete_topic(topic_id: int, db: DbSession, _admin: AdminUser) -> None:
    topic = _get_topic(db, topic_id)
    db.delete(topic)
    db.commit()


@router.post(
    "/courses/{course_id}/topics/reorder",
    response_model=list[TopicAdminOut],
    summary="Save a new topic order for a course",
    responses={404: {"model": ErrorResponse, "description": "No such course"}},
)
def reorder_topics(
    course_id: int, payload: TopicReorderRequest, db: DbSession, _admin: AdminUser
) -> list[TopicAdminOut]:
    _get_course(db, course_id)
    admin_service.reorder_topics(db, course_id, payload.ordered_ids)
    return [TopicAdminOut(**row) for row in admin_service.list_topics_admin(db, course_id)]


# ---------------------------------------------------------------------------
# Tasks / quiz builder
# ---------------------------------------------------------------------------


@router.get(
    "/tasks",
    response_model=list[TaskAdminOut],
    summary="Tasks, filterable by topic, course or title",
)
def list_tasks(
    db: DbSession,
    _admin: AdminUser,
    search: str | None = Query(default=None, max_length=100),
    topic_id: int | None = Query(default=None),
    course_id: int | None = Query(default=None),
) -> list[TaskAdminOut]:
    rows = admin_service.list_tasks_admin(
        db, search=search, topic_id=topic_id, course_id=course_id
    )
    return [TaskAdminOut(**row) for row in rows]


@router.get(
    "/tasks/{task_id}",
    response_model=TaskAdminDetail,
    summary="One task with its full question set",
    responses={404: {"model": ErrorResponse, "description": "No such task"}},
)
def read_task(task_id: int, db: DbSession, _admin: AdminUser) -> TaskAdminDetail:
    return TaskAdminDetail(**admin_service.task_admin_detail(_get_task(db, task_id)))


@router.post(
    "/tasks",
    response_model=TaskAdminDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create a quiz task",
    responses={404: {"model": ErrorResponse, "description": "No such topic"}},
)
def create_task(payload: TaskWrite, db: DbSession, _admin: AdminUser) -> TaskAdminDetail:
    _get_topic(db, payload.topic_id)
    task = Task(
        topic_id=payload.topic_id,
        title=payload.title,
        type=TaskType.quiz,
        pass_percent=payload.pass_percent,
        reward=payload.reward,
        is_active=payload.is_active,
        config=admin_service.build_quiz_config(payload.questions),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskAdminDetail(**admin_service.task_admin_detail(_get_task(db, task.id)))


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskAdminDetail,
    summary="Update a task and, optionally, replace its questions",
    responses={404: {"model": ErrorResponse, "description": "No such task"}},
)
def update_task(
    task_id: int, payload: TaskUpdate, db: DbSession, _admin: AdminUser
) -> TaskAdminDetail:
    task = _get_task(db, task_id)
    changes = payload.model_dump(exclude_none=True)

    if "topic_id" in changes:
        _get_topic(db, changes["topic_id"])
    if "questions" in changes:
        questions = payload.questions or []
        task.config = admin_service.build_quiz_config(questions)
        changes.pop("questions")

    for field, value in changes.items():
        setattr(task, field, value.strip() if isinstance(value, str) else value)

    db.add(task)
    db.commit()
    return TaskAdminDetail(**admin_service.task_admin_detail(_get_task(db, task_id)))


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task and its attempts",
    responses={404: {"model": ErrorResponse, "description": "No such task"}},
)
def delete_task(task_id: int, db: DbSession, _admin: AdminUser) -> None:
    task = _get_task(db, task_id)
    db.delete(task)
    db.commit()


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


@router.get(
    "/users",
    response_model=Page[AdminUserOut],
    summary="Search accounts, newest first",
)
def list_users(
    db: DbSession,
    _admin: AdminUser,
    search: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Page[AdminUserOut]:
    rows, total = admin_service.list_users_admin(db, search=search, limit=limit, offset=offset)
    return Page[AdminUserOut](
        items=[AdminUserOut(**row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.patch(
    "/users/{user_id}",
    response_model=AdminUserOut,
    summary="Grant/revoke admin, extend or remove a subscription",
    responses={404: {"model": ErrorResponse, "description": "No such user"}},
)
def update_user(
    user_id: int, payload: AdminUserUpdate, db: DbSession, _admin: AdminUser
) -> AdminUserOut:
    user = db.get(User, user_id)
    if user is None:
        raise _NOT_FOUND

    if payload.is_admin is not None:
        user.is_admin = payload.is_admin

    if payload.revoke_subscription:
        user.subscribed_until = None
        db.add(user)
        db.commit()

    if payload.grant_subscription_days:
        activate_subscription(
            db,
            user_id=user.id,
            days=payload.grant_subscription_days,
            amount_paise=0,
            provider_ref=f"admin-grant-{user.id}-{utcnow().isoformat()}",
            note=f"Granted by admin for {payload.grant_subscription_days} days",
        )

    db.refresh(user)
    return AdminUserOut(**admin_service.user_admin_out(db, user))


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


@router.get(
    "/reports/overview",
    response_model=ReportOverview,
    summary="Revenue, reward spend, users and recent ledger activity",
)
def read_overview(db: DbSession, _admin: AdminUser) -> ReportOverview:
    live = runtime_settings(db)
    return ReportOverview(
        **admin_service.report_overview(
            db,
            warning_threshold_percent=live.reward_max_percent_of_revenue,
            rewards_enabled=live.rewards_enabled,
        )
    )


# ---------------------------------------------------------------------------
# Runtime settings
# ---------------------------------------------------------------------------


@router.get(
    "/settings",
    response_model=list[SettingOut],
    summary="Every tunable business setting with its effective value",
)
def read_settings(db: DbSession, _admin: AdminUser) -> list[SettingOut]:
    return [SettingOut(**row) for row in describe(db)]


@router.patch(
    "/settings",
    response_model=list[SettingOut],
    summary="Change one or more settings",
    responses={422: {"model": ErrorResponse, "description": "Invalid value"}},
)
def write_settings(
    payload: SettingsUpdateRequest, db: DbSession, admin: AdminUser
) -> list[SettingOut]:
    try:
        update_settings(db, payload.values, updated_by=admin.id)
    except SettingError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return [SettingOut(**row) for row in describe(db)]


@router.post(
    "/settings/{key}/reset",
    response_model=list[SettingOut],
    summary="Reset one setting back to its environment default",
    responses={404: {"model": ErrorResponse, "description": "Unknown setting"}},
)
def reset_one_setting(key: str, db: DbSession, admin: AdminUser) -> list[SettingOut]:
    try:
        reset_setting(db, key, updated_by=admin.id)
    except SettingError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [SettingOut(**row) for row in describe(db)]
