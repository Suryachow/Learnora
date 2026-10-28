"""Course catalogue queries and the public (answer-free) views of tasks."""

from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..models import Course, Task, Topic
from ..models.progress import TopicProgress
from ..schemas.attempt import QuizOut, QuizQuestionOut
from ..schemas.learning import (
    CategorySummary,
    CourseDetail,
    CourseSummary,
    TaskPublic,
    TopicDetail,
    TopicSummary,
)
from .grading import quiz_questions
from .progress import progress_out


def _active_tasks(topic: Topic) -> list[Task]:
    """Only active tasks count towards what a learner can earn."""
    return [task for task in topic.tasks if task.is_active]


def to_task_public(task: Task) -> TaskPublic:
    """Never includes `config`: quiz answers and coding test cases stay server-side."""
    questions = (task.config or {}).get("questions") or []
    return TaskPublic(
        id=task.id,
        topic_id=task.topic_id,
        title=task.title,
        type=task.type,
        pass_percent=task.pass_percent,
        reward=task.reward,
        question_count=len(questions),
    )


def to_quiz_public(task: Task) -> QuizOut:
    """The questions a learner may answer - with the correct option stripped."""
    questions = [
        QuizQuestionOut(
            id=str(question.get("id", f"q{index + 1}")),
            prompt=str(question.get("prompt", "")),
            options=[str(option) for option in (question.get("options") or [])],
            points=max(1, int(question.get("points", 1) or 1)),
        )
        for index, question in enumerate(quiz_questions(task))
    ]
    return QuizOut(
        task_id=task.id,
        title=task.title,
        pass_percent=task.pass_percent,
        reward=task.reward,
        questions=questions,
    )


def to_topic_summary(topic: Topic) -> TopicSummary:
    return TopicSummary(
        id=topic.id,
        title=topic.title,
        position=topic.position,
        has_video=bool(topic.video_url),
        task_count=len(_active_tasks(topic)),
    )


def to_topic_detail(
    topic: Topic, progress: TopicProgress | None = None, *, has_access: bool = True
) -> TopicDetail:
    """The lesson body is withheld until a paid course has been bought."""
    locked = not has_access
    tasks = [to_task_public(task) for task in _active_tasks(topic)]
    return TopicDetail(
        id=topic.id,
        course_id=topic.course_id,
        course_title=topic.course.title,
        title=topic.title,
        content="" if locked else topic.content,
        video_url=None if locked else topic.video_url,
        position=topic.position,
        total_reward=sum(task.reward for task in tasks),
        tasks=tasks,
        is_locked=locked,
        has_course_access=has_access,
        requires_subscription=topic.course.price_paise <= 0,
        course_price_paise=topic.course.price_paise,
        progress=progress_out(progress, topic.id),
    )


def to_course_summary(course: Course) -> CourseSummary:
    topics = course.topics
    tasks = [task for topic in topics for task in _active_tasks(topic)]
    return CourseSummary(
        id=course.id,
        title=course.title,
        category=course.category,
        description=course.description,
        price_paise=course.price_paise,
        cover_image_url=course.cover_image_url,
        level=course.level,
        duration_minutes=course.duration_minutes,
        outcomes=list(course.outcomes or []),
        access_days=course.access_days,
        topic_count=len(topics),
        task_count=len(tasks),
        total_reward=sum(task.reward for task in tasks),
    )


def to_course_detail(
    course: Course,
    *,
    has_access: bool = True,
    access_expires_at: datetime | None = None,
) -> CourseDetail:
    summary = to_course_summary(course)
    return CourseDetail(
        **summary.model_dump(),
        topics=[to_topic_summary(topic) for topic in course.topics],
        has_access=has_access,
        access_expires_at=access_expires_at,
    )


def _catalogue_query():
    return (
        select(Course)
        .options(selectinload(Course.topics).selectinload(Topic.tasks))
        .order_by(Course.category, Course.title)
    )


def list_categories(db: Session) -> list[CategorySummary]:
    rows = db.execute(
        select(Course.category, func.count(Course.id))
        .where(Course.is_published.is_(True))
        .group_by(Course.category)
        .order_by(Course.category)
    ).all()
    return [CategorySummary(name=name, course_count=count) for name, count in rows]


def list_courses(
    db: Session,
    *,
    category: str | None = None,
    search: str | None = None,
    include_unpublished: bool = False,
) -> list[CourseSummary]:
    statement = _catalogue_query()
    if not include_unpublished:
        statement = statement.where(Course.is_published.is_(True))
    if category:
        statement = statement.where(func.lower(Course.category) == category.strip().lower())
    if search:
        needle = f"%{search.strip().lower()}%"
        statement = statement.where(
            or_(
                func.lower(Course.title).like(needle),
                func.lower(Course.description).like(needle),
                func.lower(Course.category).like(needle),
            )
        )
    return [to_course_summary(course) for course in db.scalars(statement)]


def get_course(db: Session, course_id: int, *, include_unpublished: bool = False) -> Course | None:
    statement = _catalogue_query().where(Course.id == course_id)
    if not include_unpublished:
        statement = statement.where(Course.is_published.is_(True))
    return db.scalars(statement).first()


def get_topic(db: Session, topic_id: int, *, include_unpublished: bool = False) -> Topic | None:
    statement = (
        select(Topic)
        .options(selectinload(Topic.tasks), selectinload(Topic.course))
        .where(Topic.id == topic_id)
    )
    topic = db.scalars(statement).first()
    if topic is None:
        return None
    if not include_unpublished and not topic.course.is_published:
        return None
    return topic


def get_task(db: Session, task_id: int) -> Task | None:
    return db.get(Task, task_id)


def count_topics_with_video(db: Session) -> int:
    """How many lessons in published courses have a video to work through."""
    return (
        db.scalar(
            select(func.count(Topic.id))
            .join(Course, Course.id == Topic.course_id)
            .where(Topic.video_url.is_not(None), Course.is_published.is_(True))
        )
        or 0
    )
