"""Admin-only queries: catalogue management helpers, user management, reports.

The routers stay thin; all of the shape-turning lives here so it can be unit
tested without HTTP. Nothing in this module is safe for a learner to call - the
routes that use it are all behind `AdminUser`.
"""

from datetime import datetime, timedelta

from sqlalchemy import Integer, func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..models import (
    Attempt,
    Course,
    CoursePurchase,
    Task,
    Topic,
    TopicProgress,
    Transaction,
    TransactionKind,
    TransactionStatus,
    Understanding,
    User,
)
from ..utils import utcnow
from .grading import quiz_questions
from .ledger import WALLET_KINDS, total_revenue

# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------


def _course_stats(course: Course) -> tuple[int, int, int]:
    """(topic_count, active_task_count, total_active_reward)."""
    topics = course.topics
    tasks = [task for topic in topics for task in topic.tasks if task.is_active]
    return len(topics), len(tasks), sum(task.reward for task in tasks)


def course_admin_out(course: Course, purchase_count: int = 0) -> dict:
    topic_count, task_count, total_reward = _course_stats(course)
    return {
        "id": course.id,
        "title": course.title,
        "category": course.category,
        "description": course.description,
        "price_paise": course.price_paise,
        "cover_image_url": course.cover_image_url,
        "level": course.level,
        "duration_minutes": course.duration_minutes,
        "outcomes": list(course.outcomes or []),
        "access_days": course.access_days,
        "topic_count": topic_count,
        "task_count": task_count,
        "total_reward": total_reward,
        "purchase_count": purchase_count,
        "is_published": course.is_published,
    }


def _purchase_counts(db: Session, course_ids: list[int]) -> dict[int, int]:
    """Buyers per course in one query, rather than one query per row."""
    if not course_ids:
        return {}
    rows = db.execute(
        select(CoursePurchase.course_id, func.count(CoursePurchase.id))
        .where(CoursePurchase.course_id.in_(course_ids))
        .group_by(CoursePurchase.course_id)
    ).all()
    return {course_id: int(count) for course_id, count in rows}


def purchase_count(db: Session, course_id: int) -> int:
    return _purchase_counts(db, [course_id]).get(course_id, 0)


def list_courses_admin(db: Session, *, search: str | None = None) -> list[dict]:
    statement = (
        select(Course)
        .options(selectinload(Course.topics).selectinload(Topic.tasks))
        .order_by(Course.category, Course.title)
    )
    if search:
        needle = f"%{search.strip().lower()}%"
        statement = statement.where(
            or_(func.lower(Course.title).like(needle), func.lower(Course.category).like(needle))
        )
    courses = list(db.scalars(statement))
    counts = _purchase_counts(db, [course.id for course in courses])
    return [course_admin_out(course, counts.get(course.id, 0)) for course in courses]


def get_course_full(db: Session, course_id: int) -> Course | None:
    statement = (
        select(Course)
        .options(selectinload(Course.topics).selectinload(Topic.tasks))
        .where(Course.id == course_id)
    )
    return db.scalars(statement).first()


def topic_admin_out(topic: Topic) -> dict:
    return {
        "id": topic.id,
        "course_id": topic.course_id,
        "course_title": topic.course.title,
        "title": topic.title,
        "position": topic.position,
        "video_url": topic.video_url,
        "content": topic.content,
        "task_count": len(topic.tasks),
    }


def list_topics_admin(db: Session, course_id: int) -> list[dict]:
    course = get_course_full(db, course_id)
    if course is None:
        return []
    return [topic_admin_out(topic) for topic in course.topics]


def get_topic_full(db: Session, topic_id: int) -> Topic | None:
    statement = (
        select(Topic)
        .options(selectinload(Topic.tasks), selectinload(Topic.course))
        .where(Topic.id == topic_id)
    )
    return db.scalars(statement).first()


def next_topic_position(db: Session, course_id: int) -> int:
    highest = db.scalar(
        select(func.max(Topic.position)).where(Topic.course_id == course_id)
    )
    return int(highest) + 1 if highest is not None else 0


def reorder_topics(db: Session, course_id: int, ordered_ids: list[int]) -> None:
    """Apply a new order. Ids that do not belong to the course are ignored."""
    course = db.get(Course, course_id)
    if course is None:
        return
    own = {topic.id: topic for topic in course.topics}
    for position, topic_id in enumerate(ordered_ids):
        topic = own.get(topic_id)
        if topic is not None:
            topic.position = position
    db.commit()


# ---------------------------------------------------------------------------
# Tasks / quiz builder
# ---------------------------------------------------------------------------


def _reward_claim_counts(db: Session) -> dict[int, int]:
    rows = db.execute(
        select(Transaction.task_id, func.count(Transaction.id))
        .where(Transaction.kind == TransactionKind.reward, Transaction.amount > 0)
        .group_by(Transaction.task_id)
    ).all()
    return {task_id: count for task_id, count in rows if task_id is not None}


def task_admin_out(task: Task, *, reward_claims: int = 0) -> dict:
    return {
        "id": task.id,
        "topic_id": task.topic_id,
        "topic_title": task.topic.title,
        "course_id": task.topic.course_id,
        "course_title": task.topic.course.title,
        "title": task.title,
        "type": task.type,
        "pass_percent": task.pass_percent,
        "reward": task.reward,
        "is_active": task.is_active,
        "question_count": len(quiz_questions(task)),
        "reward_claim_count": reward_claims,
    }


def _task_query():
    return select(Task).options(
        selectinload(Task.topic).selectinload(Topic.course)
    ).order_by(Task.topic_id, Task.id)


def list_tasks_admin(
    db: Session,
    *,
    search: str | None = None,
    topic_id: int | None = None,
    course_id: int | None = None,
) -> list[dict]:
    statement = _task_query()
    if topic_id is not None:
        statement = statement.where(Task.topic_id == topic_id)
    if course_id is not None:
        statement = statement.join(Topic, Task.topic_id == Topic.id).where(
            Topic.course_id == course_id
        )
    if search:
        needle = f"%{search.strip().lower()}%"
        statement = statement.join(Topic, Task.topic_id == Topic.id).where(
            func.lower(Task.title).like(needle)
        )
    counts = _reward_claim_counts(db)
    return [
        task_admin_out(task, reward_claims=counts.get(task.id, 0))
        for task in db.scalars(statement).unique()
    ]


def get_task_full(db: Session, task_id: int) -> Task | None:
    return db.scalars(_task_query().where(Task.id == task_id)).first()


def task_admin_detail(task: Task) -> dict:
    detail = task_admin_out(task)
    detail["questions"] = [
        {
            "id": str(question.get("id", f"q{index + 1}")),
            "prompt": str(question.get("prompt", "")),
            "options": [str(option) for option in (question.get("options") or [])],
            "correct_index": int(question.get("correct_index", 0) or 0),
            "points": max(1, int(question.get("points", 1) or 1)),
        }
        for index, question in enumerate(quiz_questions(task))
    ]
    return detail


def build_quiz_config(questions: list) -> dict:
    """Normalise the admin's questions into the stored `config` payload."""
    cleaned = []
    for index, question in enumerate(questions):
        data = question.model_dump() if hasattr(question, "model_dump") else dict(question)
        cleaned.append(
            {
                "id": str(data.get("id") or f"q{index + 1}"),
                "prompt": str(data["prompt"]),
                "options": [str(option) for option in data["options"]],
                "correct_index": int(data["correct_index"]),
                "points": max(1, int(data.get("points", 1) or 1)),
            }
        )
    return {"questions": cleaned}


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


def _user_stats(db: Session, user_ids: list[int]) -> dict[int, dict]:
    if not user_ids:
        return {}

    stats: dict[int, dict] = {
        uid: {"balance": 0, "lifetime": 0, "attempts": 0, "passed": 0} for uid in user_ids
    }

    balance_rows = db.execute(
        select(Transaction.user_id, func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id.in_(user_ids),
            Transaction.kind.in_(WALLET_KINDS),
            Transaction.status == TransactionStatus.completed,
        )
        .group_by(Transaction.user_id)
    ).all()
    for user_id, total in balance_rows:
        stats[user_id]["balance"] = int(total or 0)

    lifetime_rows = db.execute(
        select(Transaction.user_id, func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id.in_(user_ids),
            Transaction.kind == TransactionKind.reward,
            Transaction.status == TransactionStatus.completed,
            Transaction.amount > 0,
        )
        .group_by(Transaction.user_id)
    ).all()
    for user_id, total in lifetime_rows:
        stats[user_id]["lifetime"] = int(total or 0)

    attempt_rows = db.execute(
        select(
            Attempt.user_id,
            func.count(Attempt.id),
            func.coalesce(func.sum(func.cast(Attempt.passed, Integer)), 0),
        )
        .where(Attempt.user_id.in_(user_ids))
        .group_by(Attempt.user_id)
    ).all()
    for user_id, count, passed in attempt_rows:
        stats[user_id]["attempts"] = int(count or 0)
        stats[user_id]["passed"] = int(passed or 0)

    return stats


def user_admin_out(db: Session, user: User, *, stats: dict | None = None) -> dict:
    stats = stats if stats is not None else _user_stats(db, [user.id]).get(
        user.id, {"balance": 0, "lifetime": 0, "attempts": 0, "passed": 0}
    )
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "is_admin": user.is_admin,
        "has_active_subscription": user.has_active_subscription,
        "subscribed_until": user.subscribed_until,
        "created_at": user.created_at,
        "wallet_balance_paise": stats["balance"],
        "lifetime_earned_paise": stats["lifetime"],
        "attempt_count": stats["attempts"],
        "passed_count": stats["passed"],
    }


def list_users_admin(
    db: Session, *, search: str | None = None, limit: int = 25, offset: int = 0
) -> tuple[list[dict], int]:
    filters = []
    if search:
        needle = f"%{search.strip().lower()}%"
        filters.append(
            or_(func.lower(User.name).like(needle), func.lower(User.email).like(needle))
        )

    users = list(
        db.scalars(
            select(User)
            .where(*filters)
            .order_by(User.created_at.desc(), User.id.desc())
            .limit(limit)
            .offset(offset)
        )
    )
    total = int(db.scalar(select(func.count(User.id)).where(*filters)) or 0)
    stats = _user_stats(db, [user.id for user in users])
    return [user_admin_out(db, user, stats=stats.get(user.id)) for user in users], total


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


def _reward_totals(db: Session) -> tuple[int, int]:
    """(all-time rewards paid, rewards paid today)."""
    total = int(
        db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.kind == TransactionKind.reward,
                Transaction.status == TransactionStatus.completed,
                Transaction.amount > 0,
            )
        )
        or 0
    )
    return total, _rewards_today(db)


def _rewards_today(db: Session) -> int:
    start_of_day = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return int(
        db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.kind == TransactionKind.reward,
                Transaction.amount > 0,
                Transaction.created_at >= start_of_day,
            )
        )
        or 0
    )


def _daily_series(db: Session, days: int = 30) -> list[dict]:
    """One row per day: money in, rewards out, signups and quiz attempts."""
    start = (utcnow() - timedelta(days=days - 1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    buckets: dict[str, dict[str, int]] = {}
    for index in range(days):
        label = (start + timedelta(days=index)).strftime("%Y-%m-%d")
        buckets[label] = {
            "revenue_paise": 0,
            "rewards_paise": 0,
            "signups": 0,
            "attempts": 0,
        }

    day = func.date(Transaction.created_at)
    rows = db.execute(
        select(day, Transaction.kind, func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.created_at >= start,
            Transaction.status == TransactionStatus.completed,
            Transaction.kind.in_(
                [
                    TransactionKind.subscription,
                    TransactionKind.reward,
                    TransactionKind.course_purchase,
                    TransactionKind.course_payment,
                ]
            ),
        )
        .group_by(day, Transaction.kind)
    ).all()

    for raw_day, kind, total in rows:
        bucket = buckets.get(str(raw_day)[:10])
        if bucket is None:
            continue
        if kind == TransactionKind.reward:
            bucket["rewards_paise"] += int(total or 0)
        else:
            # Subscriptions arrive positive; a course sale is a negative row.
            bucket["revenue_paise"] += abs(int(total or 0))

    signup_day = func.date(User.created_at)
    for raw_day, count in db.execute(
        select(signup_day, func.count(User.id))
        .where(User.created_at >= start)
        .group_by(signup_day)
    ).all():
        bucket = buckets.get(str(raw_day)[:10])
        if bucket is not None:
            bucket["signups"] += int(count or 0)

    attempt_day = func.date(Attempt.created_at)
    for raw_day, count in db.execute(
        select(attempt_day, func.count(Attempt.id))
        .where(Attempt.created_at >= start)
        .group_by(attempt_day)
    ).all():
        bucket = buckets.get(str(raw_day)[:10])
        if bucket is not None:
            bucket["attempts"] += int(count or 0)

    return [{"day": label, **values} for label, values in buckets.items()]


def _window_totals(db: Session, since: datetime, until: datetime) -> dict[str, int]:
    """Revenue, rewards, attempts and signups inside one half-open window."""

    def money(kind: TransactionKind, *, absolute: bool = False) -> int:
        total = int(
            db.scalar(
                select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                    Transaction.kind == kind,
                    Transaction.status == TransactionStatus.completed,
                    Transaction.created_at >= since,
                    Transaction.created_at < until,
                )
            )
            or 0
        )
        return abs(total) if absolute else total

    return {
        "revenue_paise": money(TransactionKind.subscription)
        + money(TransactionKind.course_purchase, absolute=True)
        + money(TransactionKind.course_payment, absolute=True),
        "rewards_paise": money(TransactionKind.reward),
        "attempts": int(
            db.scalar(
                select(func.count(Attempt.id)).where(
                    Attempt.created_at >= since, Attempt.created_at < until
                )
            )
            or 0
        ),
        "signups": int(
            db.scalar(
                select(func.count(User.id)).where(
                    User.created_at >= since, User.created_at < until
                )
            )
            or 0
        ),
    }


def _growth(db: Session, days: int = 30) -> dict:
    """This window against the one before it, for the delta badges."""
    end = utcnow()
    start = end - timedelta(days=days)
    return {
        "days": days,
        "current": _window_totals(db, start, end),
        "previous": _window_totals(db, start - timedelta(days=days), start),
    }


def _active_learners(db: Session, days: int = 7) -> int:
    since = utcnow() - timedelta(days=days)
    return int(
        db.scalar(
            select(func.count(func.distinct(Attempt.user_id))).where(
                Attempt.created_at >= since
            )
        )
        or 0
    )


def _funnel(db: Session) -> list[dict]:
    """How far learners get: watched, checked in, attempted, passed."""
    watched = int(
        db.scalar(
            select(func.count(TopicProgress.id)).where(
                TopicProgress.video_completed_at.is_not(None)
            )
        )
        or 0
    )
    checked_in = int(
        db.scalar(
            select(func.count(TopicProgress.id)).where(
                TopicProgress.understanding.is_not(None)
            )
        )
        or 0
    )
    attempted = int(db.scalar(select(func.count(Attempt.id))) or 0)
    passed = int(
        db.scalar(select(func.count(Attempt.id)).where(Attempt.passed.is_(True))) or 0
    )
    return [
        {"label": "Videos finished", "count": watched},
        {"label": "Check-ins answered", "count": checked_in},
        {"label": "Quizzes attempted", "count": attempted},
        {"label": "Quizzes passed", "count": passed},
    ]


def _top_courses(db: Session, limit: int = 5) -> list[dict]:
    """The courses pulling their weight, by quiz attempts."""
    rows = db.execute(
        select(
            Course.id,
            Course.title,
            Course.category,
            func.count(Attempt.id).label("attempts"),
            func.coalesce(func.sum(func.cast(Attempt.passed, Integer)), 0).label("passed"),
            func.count(func.distinct(Attempt.user_id)).label("learners"),
        )
        .join(Topic, Topic.course_id == Course.id)
        .join(Task, Task.topic_id == Topic.id)
        .join(Attempt, Attempt.task_id == Task.id)
        .group_by(Course.id, Course.title, Course.category)
        .order_by(func.count(Attempt.id).desc(), Course.title)
        .limit(limit)
    ).all()

    rewards = {
        course_id: int(total or 0)
        for course_id, total in db.execute(
            select(Topic.course_id, func.coalesce(func.sum(Transaction.amount), 0))
            .join(Task, Task.id == Transaction.task_id)
            .join(Topic, Topic.id == Task.topic_id)
            .where(
                Transaction.kind == TransactionKind.reward,
                Transaction.status == TransactionStatus.completed,
                Transaction.amount > 0,
            )
            .group_by(Topic.course_id)
        ).all()
    }

    return [
        {
            "id": course_id,
            "title": title,
            "category": category,
            "learners": int(learners or 0),
            "attempts": int(attempts or 0),
            "passed": int(passed or 0),
            "rewards_paise": rewards.get(course_id, 0),
        }
        for course_id, title, category, attempts, passed, learners in rows
    ]


def _top_learners(db: Session, limit: int = 5) -> list[dict]:
    rows = db.execute(
        select(
            User.id,
            User.name,
            User.email,
            func.coalesce(func.sum(Transaction.amount), 0).label("earned"),
        )
        .join(Transaction, Transaction.user_id == User.id)
        .where(
            Transaction.kind == TransactionKind.reward,
            Transaction.status == TransactionStatus.completed,
            Transaction.amount > 0,
        )
        .group_by(User.id, User.name, User.email)
        .order_by(func.coalesce(func.sum(Transaction.amount), 0).desc(), User.name)
        .limit(limit)
    ).all()

    stats = _user_stats(db, [user_id for user_id, *_ in rows])
    return [
        {
            "id": user_id,
            "name": name,
            "email": email,
            "rewards_paise": int(earned or 0),
            "attempts": stats.get(user_id, {}).get("attempts", 0),
            "passed": stats.get(user_id, {}).get("passed", 0),
        }
        for user_id, name, email, earned in rows
    ]


def _recent_attempts(db: Session, limit: int = 6) -> list[dict]:
    rows = db.execute(
        select(Attempt, User, Task, Topic, Course)
        .join(User, User.id == Attempt.user_id)
        .join(Task, Task.id == Attempt.task_id)
        .join(Topic, Topic.id == Task.topic_id)
        .join(Course, Course.id == Topic.course_id)
        .order_by(Attempt.created_at.desc(), Attempt.id.desc())
        .limit(limit)
    ).all()
    return [
        {
            "id": attempt.id,
            "user_name": user.name,
            "task_title": task.title,
            "course_title": course.title,
            "percent": attempt.percent,
            "passed": attempt.passed,
            "created_at": attempt.created_at,
        }
        for attempt, user, task, _topic, course in rows
    ]


def _recent_transactions(db: Session, limit: int = 10) -> list[dict]:
    rows = db.execute(
        select(Transaction, User)
        .join(User, Transaction.user_id == User.id)
        .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        .limit(limit)
    ).all()
    return [
        {
            "id": transaction.id,
            "user_id": user.id,
            "user_name": user.name,
            "user_email": user.email,
            "kind": transaction.kind.value,
            "amount": transaction.amount,
            "status": transaction.status.value,
            "note": transaction.note,
            "created_at": transaction.created_at,
        }
        for transaction, user in rows
    ]


def _understanding_counts(db: Session) -> list[dict]:
    """How learners rated their own understanding, always in the same order."""
    counts = {
        rating: int(count)
        for rating, count in db.execute(
            select(TopicProgress.understanding, func.count(TopicProgress.id))
            .where(TopicProgress.understanding.is_not(None))
            .group_by(TopicProgress.understanding)
        ).all()
    }
    return [
        {"rating": rating.value, "count": counts.get(rating, 0)}
        for rating in Understanding
    ]


def report_overview(db: Session, *, warning_threshold_percent: int, rewards_enabled: bool) -> dict:
    revenue = total_revenue(db)
    rewards_paid, rewards_today = _reward_totals(db)
    if revenue > 0:
        ratio = round(rewards_paid / revenue * 100, 2)
    else:
        ratio = 100.0 if rewards_paid > 0 else 0.0

    total_attempts = int(db.scalar(select(func.count(Attempt.id))) or 0)
    passed_attempts = int(
        db.scalar(select(func.count(Attempt.id)).where(Attempt.passed.is_(True))) or 0
    )

    return {
        "revenue_paise": revenue,
        "rewards_paid_paise": rewards_paid,
        "rewards_today_paise": rewards_today,
        "reward_ratio_percent": ratio,
        "reward_ratio_warning": ratio > warning_threshold_percent,
        "warning_threshold_percent": warning_threshold_percent,
        "rewards_enabled": rewards_enabled,
        "total_users": int(db.scalar(select(func.count(User.id))) or 0),
        "subscribed_users": int(
            db.scalar(
                select(func.count(User.id)).where(User.subscribed_until > utcnow())
            )
            or 0
        ),
        "total_attempts": total_attempts,
        "passed_attempts": passed_attempts,
        "pass_rate_percent": round(passed_attempts / total_attempts * 100, 2)
        if total_attempts
        else 0.0,
        "course_count": int(db.scalar(select(func.count(Course.id))) or 0),
        "topic_count": int(db.scalar(select(func.count(Topic.id))) or 0),
        "task_count": int(db.scalar(select(func.count(Task.id))) or 0),
        "active_task_count": int(
            db.scalar(select(func.count(Task.id)).where(Task.is_active.is_(True))) or 0
        ),
        "video_completions": int(
            db.scalar(
                select(func.count(TopicProgress.id)).where(
                    TopicProgress.video_completed_at.is_not(None)
                )
            )
            or 0
        ),
        "understanding_counts": _understanding_counts(db),
        "recent_transactions": _recent_transactions(db),
        "recent_attempts": _recent_attempts(db),
        "funnel": _funnel(db),
        "top_courses": _top_courses(db),
        "top_learners": _top_learners(db),
        "growth": _growth(db),
        "active_learners_7d": _active_learners(db),
        "daily": _daily_series(db),
    }
