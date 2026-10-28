"""Assessment payloads.

`QuizOut` is the *only* shape a learner ever receives before submitting, and it
deliberately has no `correct_index`: the answers never leave the server.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class QuizQuestionOut(BaseModel):
    """A question as the learner sees it - the correct option is not included."""

    id: str
    prompt: str
    options: list[str]
    points: int = 1


class QuizOut(BaseModel):
    task_id: int
    title: str
    pass_percent: int
    reward: int
    questions: list[QuizQuestionOut]


class AttemptSubmitRequest(BaseModel):
    """`answers` maps a question id to the index of the chosen option."""

    answers: dict[str, int] = Field(default_factory=dict)


class AttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    task_title: str | None = None
    percent: int
    passed: bool
    created_at: datetime


class AttemptResultOut(BaseModel):
    """The outcome of one submission, including what the reward did."""

    attempt: AttemptOut
    percent: int
    passed: bool
    correct_count: int
    question_count: int
    reward_paise: int
    reward_granted: bool
    reward_reason: str
    message: str


class AttemptSummaryOut(BaseModel):
    """Progress derived from attempts - never stored, so it cannot drift."""

    total_attempts: int
    passed_tasks: int
    best_percent: int | None = None
