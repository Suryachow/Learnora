"""Write the catalogue's quizzes with Groq.

Quiz generation runs here rather than in the API: questions are graded on the
server, so they have to be stored once and stay identical between attempts.

    python scripts/generate_quizzes.py                 # rewrite every quiz
    python scripts/generate_quizzes.py --missing-only  # only lessons without one
    python scripts/generate_quizzes.py --course C --limit 2
    python scripts/generate_quizzes.py --topic pointers --dry-run

Requires GROQ_API_KEY in backend/.env (or the environment). Without it the
script stops and says so, leaving the seeded quizzes untouched.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session, selectinload  # noqa: E402

from app.config import settings  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.models import Course, Task, TaskType, Topic  # noqa: E402
from app.services.admin import build_quiz_config  # noqa: E402
from app.services.quizgen import (  # noqa: E402
    QuizGenerationError,
    build_prompt,
    generate_questions,
)

DEFAULT_REWARD_PAISE = 2500


def _topics(db: Session, *, course: str | None, topic: str | None) -> list[Topic]:
    statement = (
        select(Topic)
        .join(Course, Course.id == Topic.course_id)
        .options(selectinload(Topic.tasks), selectinload(Topic.course))
        .where(Course.is_published.is_(True))
        .order_by(Course.category, Topic.position)
    )
    if course:
        needle = course.strip().lower()
        statement = statement.where(
            (Course.category.ilike(f"%{needle}%")) | (Course.title.ilike(f"%{needle}%"))
        )
    if topic:
        statement = statement.where(Topic.title.ilike(f"%{topic.strip()}%"))
    return list(db.scalars(statement))


def _quiz_task(topic: Topic) -> Task | None:
    return next((task for task in topic.tasks if task.type == TaskType.quiz), None)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate quiz questions with Groq.")
    parser.add_argument("--course", help="Filter by course title or category, e.g. C")
    parser.add_argument("--topic", help="Filter by part of a lesson title")
    parser.add_argument(
        "--missing-only",
        action="store_true",
        help="Only fill lessons that have no quiz task yet",
    )
    parser.add_argument("--limit", type=int, default=0, help="Stop after N lessons")
    parser.add_argument(
        "--count",
        type=int,
        default=settings.quiz_questions_per_topic,
        help="Questions per lesson",
    )
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds between calls")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the prompt for the first lesson and exit",
    )
    args = parser.parse_args(argv)

    with SessionLocal() as db:
        topics = _topics(db, course=args.course, topic=args.topic)
        if args.limit:
            topics = topics[: args.limit]
        if not topics:
            print("No lessons matched. Check --course / --topic.", file=sys.stderr)
            return 1

        if args.dry_run:
            print(f"{len(topics)} lesson(s) matched:")
            for topic in topics:
                state = "has a quiz" if _quiz_task(topic) else "no quiz"
                print(f"  - {topic.course.category} / {topic.title} ({state})")
            topic = topics[0]
            print("\nPrompt that would be sent for the first lesson:\n")
            print(
                build_prompt(
                    course_title=topic.course.title,
                    topic_title=topic.title,
                    content=topic.content or topic.title,
                    count=args.count,
                )
            )
            return 0

        if not settings.groq_configured:
            print(
                "GROQ_API_KEY is not set.\n"
                "Add it to backend/.env (GROQ_API_KEY=gsk_...) and run this again.\n"
                "The quizzes shipped with scripts/seed.py stay in place until then.",
                file=sys.stderr,
            )
            return 2

        updated = created = skipped = failed = 0
        print(f"Writing {args.count} questions for {len(topics)} lesson(s) with {settings.groq_model}.")

        for position, topic in enumerate(topics, start=1):
            task = _quiz_task(topic)
            if args.missing_only and task is not None:
                skipped += 1
                continue
            try:
                questions = generate_questions(
                    course_title=topic.course.title,
                    topic_title=topic.title,
                    content=topic.content or topic.title,
                    count=args.count,
                )
            except QuizGenerationError as error:
                failed += 1
                print(f"  [{position}/{len(topics)}] ! {topic.title}: {error}", file=sys.stderr)
                continue

            if task is None:
                task = Task(
                    topic_id=topic.id,
                    title=f"{topic.title} check",
                    type=TaskType.quiz,
                    pass_percent=70,
                    reward=DEFAULT_REWARD_PAISE,
                    is_active=True,
                    config=build_quiz_config(questions),
                )
                db.add(task)
                created += 1
                print(f"  [{position}/{len(topics)}] + {topic.title} ({len(questions)} questions)")
            else:
                task.config = build_quiz_config(questions)
                updated += 1
                print(f"  [{position}/{len(topics)}] ~ {topic.title} ({len(questions)} questions)")

            db.commit()
            if args.delay and position < len(topics):
                time.sleep(args.delay)

    if args.missing_only and skipped:
        print(f"Skipped {skipped} lesson(s) that already had a quiz.")
    print(f"Done. {updated} rewritten, {created} created, {failed} failed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
