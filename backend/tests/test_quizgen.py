"""Quiz generation is tested against a stub transport, never the real Groq API."""

import json

import httpx
import pytest

from app.config import settings
from app.services import quizgen
from app.services.quizgen import (
    QuizGenerationError,
    generate_questions,
    normalise_questions,
)

VALID = {
    "questions": [
        {
            "prompt": "What does malloc return on failure?",
            "options": ["NULL", "0 bytes", "-1", "An empty block"],
            "correct_index": 0,
        },
        {
            "prompt": "Which call allocates zeroed memory?",
            "options": ["malloc", "calloc", "realloc", "free"],
            "correct_index": 1,
        },
        {
            "prompt": "What must follow every successful allocation?",
            "options": ["free", "memset", "realloc", "another malloc"],
            "correct_index": 0,
        },
    ]
}


def _reply(content: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={"choices": [{"message": {"role": "assistant", "content": content}}]},
    )


def test_normalise_accepts_a_wrapped_object():
    questions = normalise_questions(VALID)
    assert len(questions) == 3
    assert questions[0]["correct_index"] == 0


def test_normalise_accepts_a_bare_list():
    assert len(normalise_questions(VALID["questions"])) == 3


def test_normalise_drops_questions_that_cannot_be_graded():
    payload = {
        "questions": [
            {"prompt": "Too few options", "options": ["a", "b"], "correct_index": 0},
            {
                "prompt": "Repeated options",
                "options": ["a", "a", "b", "c"],
                "correct_index": 1,
            },
            {
                "prompt": "Index out of range",
                "options": ["a", "b", "c", "d"],
                "correct_index": 7,
            },
            VALID["questions"][0],
        ]
    }
    questions = normalise_questions(payload)
    assert [question["prompt"] for question in questions] == [VALID["questions"][0]["prompt"]]


def test_normalise_rejects_fewer_than_one_usable_question():
    with pytest.raises(QuizGenerationError):
        normalise_questions({"questions": []})


def test_generate_refuses_without_a_key(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "")
    with pytest.raises(QuizGenerationError):
        generate_questions(course_title="C", topic_title="Pointers", content="notes")


def test_generate_parses_a_fenced_reply(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    fenced = "```json\n" + json.dumps(VALID) + "\n```"

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["response_format"] == {"type": "json_object"}
        assert request.headers["authorization"] == "Bearer test-key"
        return _reply(fenced)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        questions = generate_questions(
            course_title="C",
            topic_title="Dynamic memory",
            content="notes",
            count=3,
            client=client,
        )
    assert len(questions) == 3


def test_generate_reports_an_api_error(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text='{"error": "invalid api key"}')

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        with pytest.raises(QuizGenerationError, match="401"):
            generate_questions(
                course_title="C",
                topic_title="Pointers",
                content="notes",
                client=client,
            )


def test_generate_rejects_a_reply_that_is_not_json(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    transport = httpx.MockTransport(lambda request: _reply("Sure! Here are some questions."))
    with httpx.Client(transport=transport) as client:
        with pytest.raises(QuizGenerationError):
            generate_questions(
                course_title="C",
                topic_title="Pointers",
                content="notes",
                client=client,
            )


def test_generate_waits_out_a_throttle(monkeypatch):
    """A 429 names the wait, so the same lesson is retried instead of failing."""
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    slept: list[float] = []
    monkeypatch.setattr(quizgen.time, "sleep", lambda seconds: slept.append(seconds))

    throttled = httpx.Response(
        429, text="Rate limit reached ... Please try again in 7.02s. Need more tokens?"
    )
    replies = iter([throttled, _reply(json.dumps(VALID))])
    transport = httpx.MockTransport(lambda request: next(replies))

    with httpx.Client(transport=transport) as client:
        questions = generate_questions(
            course_title="C",
            topic_title="Pointers",
            content="notes",
            count=3,
            client=client,
        )

    assert len(questions) == 3
    assert slept == [7.02]


def test_generate_gives_up_after_repeated_throttling(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    monkeypatch.setattr(quizgen.time, "sleep", lambda seconds: None)
    transport = httpx.MockTransport(
        lambda request: httpx.Response(429, text="slow down")
    )

    with httpx.Client(transport=transport) as client:
        with pytest.raises(QuizGenerationError, match="429"):
            generate_questions(
                course_title="C",
                topic_title="Pointers",
                content="notes",
                client=client,
            )


def test_generate_does_not_retry_a_rejected_key(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(401, text='{"error": "invalid api key"}')

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        with pytest.raises(QuizGenerationError, match="401"):
            generate_questions(
                course_title="C",
                topic_title="Pointers",
                content="notes",
                client=client,
            )

    assert len(calls) == 1
