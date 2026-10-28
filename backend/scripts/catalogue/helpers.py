"""Builders shared by the course modules.

A course module only describes lessons; how those lessons reach the database is
`scripts/seed.py`'s problem. Keeping the two apart is what lets the catalogue
grow without making the seeding logic harder to follow.
"""

EMBED = "https://www.youtube.com/embed"


def Q(prompt: str, options: list[str], correct: int) -> dict:
    """A quiz question. `correct` is an index into `options`."""
    return {"prompt": prompt, "options": options, "correct_index": correct}


def quiz(title: str, reward: int, questions: list[dict], pass_percent: int = 70) -> dict:
    return {"title": title, "reward": reward, "pass_percent": pass_percent, "questions": questions}


def lesson(title: str, video: str, content: str, *tasks: dict) -> dict:
    """One lesson: the video the learner must watch through, then its quizzes.

    `video` is a bare YouTube id rather than a full URL. Every lesson carries
    one, because a lesson with no video has nothing to gate the quiz on - the
    watch-to-the-end rule only applies to material Learnora can play.

    The ids below are drawn from a small set already verified to exist, so a
    rewritten lesson can never embed a dead video. Several lessons share one
    short tour; the written material is what differs between them.
    """
    return {
        "title": title,
        "video_url": f"{EMBED}/{video}",
        "content": content,
        "tasks": list(tasks),
    }
