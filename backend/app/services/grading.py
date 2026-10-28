"""Server-side quiz grading.

The questions and their correct answers live in `Task.config` and are never sent
to the browser. Grading happens here, on the server, so the score - and the
reward that depends on it - cannot be edited by the client.
"""

from dataclasses import dataclass

from ..models import Task, TaskType


class GradingError(Exception):
    """Raised when a task cannot be graded (wrong type, or no questions)."""


@dataclass(frozen=True)
class GradeOutcome:
    percent: int
    passed: bool
    correct_count: int
    question_count: int


def quiz_questions(task: Task) -> list[dict]:
    """The raw questions, for server use only. Never return this to a client."""
    return list((task.config or {}).get("questions") or [])


def grade_quiz_submission(task: Task, answers: dict[str, int]) -> GradeOutcome:
    """Grade `answers` (question id -> chosen option index) against the task.

    Questions may carry an optional `points` weight; when none do, every
    question counts equally.
    """
    if task.type != TaskType.quiz:
        raise GradingError("Only quizzes can be graded right now.")

    questions = quiz_questions(task)
    if not questions:
        raise GradingError("This task has no questions configured yet.")

    weighted = any("points" in question for question in questions)

    earned = 0
    possible = 0
    correct_count = 0

    for index, question in enumerate(questions):
        weight = 1
        if weighted:
            try:
                weight = max(1, int(question.get("points", 1)))
            except (TypeError, ValueError):
                weight = 1
        possible += weight

        question_id = str(question.get("id", f"q{index + 1}"))
        chosen = answers.get(question_id)
        correct_index = question.get("correct_index")
        if isinstance(chosen, int) and not isinstance(chosen, bool) and chosen == correct_index:
            earned += weight
            correct_count += 1

    percent = 0 if possible <= 0 else round((earned / possible) * 100)
    percent = max(0, min(100, percent))

    return GradeOutcome(
        percent=percent,
        passed=percent >= task.pass_percent,
        correct_count=correct_count,
        question_count=len(questions),
    )
