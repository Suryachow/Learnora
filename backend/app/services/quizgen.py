"""Write quiz questions for a lesson with Groq's chat completions API.

Generation is a build-time step, not a request-time one. Questions are stored on
the task and graded on the server, so asking a model again on every attempt
would make the same quiz different each time - and unmarkable. `scripts/
generate_quizzes.py` is the only caller.

Everything the model returns is treated as untrusted: a question is kept only
when it can actually be graded (a prompt, four distinct options, one valid
index). A reply that fails those checks raises instead of writing a broken quiz.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

#: How many graded questions a reply must contain before we accept it.
MINIMUM_QUESTIONS = 3

#: How many times a throttled or unreachable request is tried before giving up.
MAX_ATTEMPTS = 6

#: A wait longer than this means the quota is spent, not that we should pause.
MAX_WAIT_SECONDS = 90.0

#: Groq puts the wait in the message: "... Please try again in 7.02s."
_WAIT_HINT = re.compile(r"try again in ([0-9.]+)\s*(ms|s)\b", re.IGNORECASE)


class QuizGenerationError(RuntimeError):
    """The model could not be reached, or it returned questions we cannot grade."""


SYSTEM_PROMPT = (
    "You write multiple-choice quizzes for a programming course. "
    "You answer with JSON only, never with prose."
)


def build_prompt(
    *, course_title: str, topic_title: str, content: str, count: int
) -> str:
    """The instruction sent with one lesson's notes."""
    return (
        f"Course: {course_title}\n"
        f"Lesson: {topic_title}\n\n"
        "Lesson notes:\n"
        f"{content}\n\n"
        f"Write exactly {count} multiple-choice questions that check whether a learner "
        "understood this lesson.\n"
        "Rules:\n"
        "- Exactly 4 options per question, exactly one correct answer.\n"
        "- Distractors must be plausible and clearly wrong; never 'all of the above'.\n"
        "- Test understanding and consequence, not trivia or exact wording.\n"
        "- Keep each prompt under 220 characters and each option under 90.\n"
        "- Vary which position holds the correct answer.\n"
        "- Use plain ASCII quotes and no markdown.\n\n"
        'Reply with JSON only: {"questions": [{"prompt": string, '
        '"options": [string, string, string, string], "correct_index": integer}]}'
    )


def _strip_fence(text: str) -> str:
    """Models occasionally wrap JSON in a ``` fence even when told not to."""
    cleaned = text.strip()
    if not cleaned.startswith("```"):
        return cleaned
    cleaned = cleaned.split("\n", 1)[-1]
    if cleaned.rstrip().endswith("```"):
        cleaned = cleaned.rstrip()[:-3]
    return cleaned.strip()


def normalise_questions(raw: Any) -> list[dict]:
    """Keep only questions the grader can mark, in the stored `config` shape."""
    if isinstance(raw, dict):
        raw = raw.get("questions")
    if not isinstance(raw, list):
        raise QuizGenerationError("The model did not return a list of questions.")

    cleaned: list[dict] = []
    seen: set[str] = set()
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        prompt = str(entry.get("prompt") or "").strip()
        options = entry.get("options")
        index = entry.get("correct_index")
        if not prompt or not isinstance(options, list) or len(options) != 4:
            continue
        texts = [str(option).strip() for option in options]
        if any(not text for text in texts) or len(set(texts)) != 4:
            continue
        try:
            correct = int(index)
        except (TypeError, ValueError):
            continue
        if not 0 <= correct < 4:
            continue
        key = prompt.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append({"prompt": prompt, "options": texts, "correct_index": correct})

    if not cleaned:
        raise QuizGenerationError("The model returned no question that could be graded.")
    return cleaned


def _wait_for(response: httpx.Response) -> float:
    """Seconds to wait before retrying, taken from the reply when it says so."""
    header = response.headers.get("retry-after")
    if header:
        try:
            return float(header)
        except ValueError:
            pass
    match = _WAIT_HINT.search(response.text)
    if match:
        value = float(match.group(1))
        return value / 1000.0 if match.group(2).lower() == "ms" else value
    return 0.0


def _pause(seconds: float, reason: str) -> None:
    seconds = max(seconds, 1.0)
    logger.warning("Groq asked us to wait %.1fs (%s)", seconds, reason)
    time.sleep(seconds)


def _post(payload: dict, *, client: httpx.Client | None = None) -> dict:
    """POST to Groq, waiting out a throttle instead of failing the lesson.

    The free tier meters *tokens* per minute, so a catalogue-wide run is throttled
    part way through however politely it paces itself. A 429 names the wait, so
    the only useful response is to sleep for it and try the same lesson again.
    """
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key.strip()}",
        "Content-Type": "application/json",
    }
    url = f"{settings.groq_base_url.rstrip('/')}/chat/completions"

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            if client is None:
                with httpx.Client(timeout=settings.quiz_generation_timeout_seconds) as owned:
                    response = owned.post(url, headers=headers, json=payload)
            else:
                response = client.post(url, headers=headers, json=payload)
        except httpx.HTTPError as error:
            if attempt == MAX_ATTEMPTS:
                raise QuizGenerationError(f"Could not reach Groq: {error}") from error
            _pause(min(2.0 * attempt, MAX_WAIT_SECONDS), f"network error: {error}")
            continue

        if response.status_code == 429 or response.status_code >= 500:
            detail = response.text[:200]
            if attempt == MAX_ATTEMPTS:
                raise QuizGenerationError(f"Groq returned {response.status_code}: {detail}")
            wait = _wait_for(response) or 2.0 * attempt
            if wait > MAX_WAIT_SECONDS:
                raise QuizGenerationError(
                    f"Groq quota looks spent - it asked us to wait {wait:.0f}s. "
                    f"Try again later, or run with --missing-only to fill the gaps."
                )
            _pause(wait, f"{response.status_code} on attempt {attempt}")
            continue

        if response.status_code >= 400:
            # 400/401/404 will not get better by asking again.
            raise QuizGenerationError(f"Groq returned {response.status_code}: {response.text[:300]}")

        try:
            return response.json()
        except ValueError as error:
            raise QuizGenerationError("Groq returned a body that was not JSON.") from error

    raise QuizGenerationError("Groq could not be reached after several attempts.")


def _read_questions(body: dict) -> list[dict]:
    """Pull markable questions out of a chat-completions reply."""
    try:
        message = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise QuizGenerationError("Groq's reply had no message content.") from error

    try:
        parsed = json.loads(_strip_fence(str(message)))
    except ValueError as error:
        raise QuizGenerationError("Groq's message was not valid JSON.") from error

    return normalise_questions(parsed)


def generate_questions(
    *,
    course_title: str,
    topic_title: str,
    content: str,
    count: int | None = None,
    client: httpx.Client | None = None,
    attempts: int = 2,
) -> list[dict]:
    """Ask Groq for a set of markable questions about one lesson.

    A reply that parses but does not contain enough gradeable questions is asked
    again rather than failing the lesson: the model sometimes answers a long
    lesson with only one or two complete questions, and trying once more is
    cheaper than leaving a lesson without a quiz.
    """
    if not settings.groq_configured:
        raise QuizGenerationError(
            "GROQ_API_KEY is not set. Add it to backend/.env to let Groq write quizzes."
        )

    wanted = count or settings.quiz_questions_per_topic
    prompt = build_prompt(
        course_title=course_title,
        topic_title=topic_title,
        content=content or topic_title,
        count=wanted,
    )
    payload = {
        "model": settings.groq_model,
        "temperature": 0.4,
        "max_tokens": 2500,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }

    problem: QuizGenerationError | None = None
    for attempt in range(1, attempts + 1):
        body = _post(payload, client=client)
        try:
            questions = _read_questions(body)
        except QuizGenerationError as error:
            problem = error
        else:
            if len(questions) >= MINIMUM_QUESTIONS:
                logger.info("Generated %s questions for %r", len(questions), topic_title)
                return questions[:wanted]
            problem = QuizGenerationError(
                f"Groq returned only {len(questions)} usable questions; need at least "
                f"{MINIMUM_QUESTIONS}."
            )
        if attempt < attempts:
            logger.warning("%s Asking again for %r.", problem, topic_title)

    raise problem or QuizGenerationError("Groq returned no usable questions.")
