"""Create the initial admin plus the shipped catalogue.

Idempotent: rows are matched by title/email, so running it twice adds nothing.
Lesson material is refreshed when the catalogue changes, which is how an
existing database picks up a new video or rewritten notes. Courses that the
catalogue no longer defines are retired here too, so a reseed leaves the
product showing exactly the two courses Learnora teaches.

Run with:

    python scripts/seed.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    Attempt,
    Course,
    CoursePurchase,
    Task,
    TaskType,
    Topic,
    TopicProgress,
    User,
)
from app.services.security import hash_password  # noqa: E402
from scripts.catalogue import CATALOGUE  # noqa: E402

ADMIN_NAME = os.getenv("SEED_ADMIN_NAME", "SkillEarn Admin")
ADMIN_EMAIL = os.getenv("SEED_ADMIN_EMAIL", "admin@skillearn.dev").lower()
ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "Admin@12345")


def _seed_admin(db: Session) -> User:
    admin = db.scalar(select(User).where(User.email == ADMIN_EMAIL))
    if admin is None:
        admin = User(
            name=ADMIN_NAME,
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
            is_admin=True,
        )
        db.add(admin)
        db.flush()
        print(f"  + admin {ADMIN_EMAIL}")
    else:
        admin.is_admin = True
        print(f"  = admin {ADMIN_EMAIL} already exists")
    return admin


def _prune_retired_topics(db: Session, course: Course, keep: set[str]) -> None:
    """Remove lessons this catalogue no longer defines.

    Renaming a lesson would otherwise leave the old row behind as a duplicate,
    usually one without a video - and a lesson with no video is one the
    watch-to-the-end rule cannot police. A lesson is only removed while nobody
    has touched it: no progress recorded, no quiz attempted.
    """
    stale = db.scalars(
        select(Topic).where(Topic.course_id == course.id, Topic.title.not_in(keep))
    ).all()
    for topic in stale:
        if db.scalar(select(TopicProgress.id).where(TopicProgress.topic_id == topic.id)):
            continue
        attempted = db.scalar(
            select(Attempt.id).where(Attempt.task_id.in_([task.id for task in topic.tasks]))
        )
        if attempted is not None:
            continue
        db.delete(topic)
        print(f"    - topic {topic.title!r} retired")


def _course_has_history(db: Session, course: Course) -> bool:
    """True when a learner has progress, an attempt or a purchase in this course."""
    topic_ids = [topic.id for topic in course.topics]
    if topic_ids and db.scalar(
        select(TopicProgress.id).where(TopicProgress.topic_id.in_(topic_ids))
    ):
        return True
    task_ids = [task.id for topic in course.topics for task in topic.tasks]
    if task_ids and db.scalar(select(Attempt.id).where(Attempt.task_id.in_(task_ids))):
        return True
    return (
        db.scalar(select(CoursePurchase.id).where(CoursePurchase.course_id == course.id))
        is not None
    )


def _prune_retired_courses(db: Session, keep: set[str]) -> None:
    """Drop courses the catalogue no longer teaches.

    A course nobody has touched is deleted with its lessons. One that carries
    learner history is unpublished instead, because deleting it would take the
    learner's attempts and balance history with it.
    """
    for course in db.scalars(select(Course).where(Course.title.not_in(keep))).all():
        if _course_has_history(db, course):
            if course.is_published:
                course.is_published = False
                print(f"  ~ course {course.title!r} hidden (learner history kept)")
            continue
        db.delete(course)
        print(f"  - course {course.title!r} retired")


def _refresh_quiz(db: Session, task: Task, task_data: dict, questions: list[dict]) -> None:
    """Bring a stored quiz in line with the catalogue.

    A rewritten quiz has to reach an existing database, but never over a
    learner's history: once a task has been attempted its questions are frozen,
    so a reseed can never change what somebody was already marked on.
    """
    unchanged = (
        task.pass_percent == task_data["pass_percent"]
        and task.reward == task_data["reward"]
        and (task.config or {}).get("questions") == questions
    )
    if unchanged:
        return
    if db.scalar(select(Attempt.id).where(Attempt.task_id == task.id)):
        print(f"      = task {task.title!r} kept (already attempted)")
        return
    task.pass_percent = task_data["pass_percent"]
    task.reward = task_data["reward"]
    task.config = {"questions": questions}
    print(f"      ~ task {task.title!r} refreshed")


def _seed_catalogue(db: Session) -> None:
    for course_data in CATALOGUE:
        price = course_data["price_paise"]
        course = db.scalar(select(Course).where(Course.title == course_data["title"]))
        if course is None:
            course = Course(
                title=course_data["title"],
                category=course_data["category"],
                description=course_data["description"],
                price_paise=price,
                is_published=True,
            )
            db.add(course)
            db.flush()
            print(f"  + course {course.title!r} ({course.category}, {price} paise)")
        else:
            if (
                course.category != course_data["category"]
                or course.description != course_data["description"]
            ):
                course.category = course_data["category"]
                course.description = course_data["description"]
                print(f"  ~ course {course.title!r} refreshed")
            # The catalogue owns the price, so a reseed is what moves a course
            # from free to paid - and keeps the shipped price honest.
            if course.price_paise != price:
                course.price_paise = price
                print(f"  ~ course {course.title!r} priced at {price} paise")

        for position, topic_data in enumerate(course_data["topics"]):
            topic = db.scalar(
                select(Topic).where(
                    Topic.course_id == course.id, Topic.title == topic_data["title"]
                )
            )
            if topic is None:
                topic = Topic(
                    course_id=course.id,
                    title=topic_data["title"],
                    content=topic_data["content"],
                    video_url=topic_data["video_url"],
                    position=position,
                )
                db.add(topic)
                db.flush()
                print(f"    + topic {topic.title!r}")
            elif (
                topic.content != topic_data["content"]
                or topic.video_url != topic_data["video_url"]
                or topic.position != position
            ):
                # Lesson material is editorial and gets revised. Refreshing it here
                # is what lets an existing database pick up a new video without a
                # migration; running the seed twice still changes nothing.
                topic.content = topic_data["content"]
                topic.video_url = topic_data["video_url"]
                topic.position = position
                print(f"    ~ topic {topic.title!r} refreshed")

            for task_data in topic_data["tasks"]:
                questions = [
                    {**question, "id": f"q{index + 1}"}
                    for index, question in enumerate(task_data["questions"])
                ]
                task = db.scalar(
                    select(Task).where(
                        Task.topic_id == topic.id, Task.title == task_data["title"]
                    )
                )
                if task is not None:
                    _refresh_quiz(db, task, task_data, questions)
                    continue
                db.add(
                    Task(
                        topic_id=topic.id,
                        title=task_data["title"],
                        type=TaskType.quiz,
                        pass_percent=task_data["pass_percent"],
                        reward=task_data["reward"],
                        is_active=True,
                        config={"questions": questions},
                    )
                )
                print(f"      + task {task_data['title']!r} (reward {task_data['reward']} paise)")

        _prune_retired_topics(db, course, {topic["title"] for topic in course_data["topics"]})


def main() -> None:
    print("Seeding Learnora...")
    with SessionLocal() as db:
        _seed_admin(db)
        _seed_catalogue(db)
        _prune_retired_courses(db, {course["title"] for course in CATALOGUE})
        db.commit()
    print(f"Done. Sign in as {ADMIN_EMAIL}")
    if not os.getenv("SEED_ADMIN_PASSWORD"):
        # Only echo the built-in development password; a configured one must never
        # end up in a container log.
        print(f"      Password: {ADMIN_PASSWORD}")


if __name__ == "__main__":
    main()
