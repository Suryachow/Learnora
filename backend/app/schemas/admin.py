"""Request/response schemas for the admin console.

These are trusted payloads: an admin may see quiz answers (to edit them) and
grant subscriptions. Every route that uses them is behind `AdminUser`.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..models import CourseLevel, TaskType
from .learning import CourseSummary

# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------


class CourseAdminOut(CourseSummary):
    is_published: bool
    #: How many learners have bought it. Free courses normally stay at 0.
    purchase_count: int = 0


def _clean_outcomes(values: list[str]) -> list[str]:
    """Trim each line, drop blanks, and keep the list readable."""
    return [line.strip() for line in values if line.strip()][:20]


#: Columns that are NOT NULL, so an explicit null in an update means "leave it".
_NOT_NULL_COURSE_FIELDS = (
    "title",
    "category",
    "description",
    "is_published",
    "price_paise",
    "level",
    "outcomes",
)


class CourseWrite(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    category: str = Field(min_length=2, max_length=100)
    description: str = ""
    is_published: bool = False
    #: What a learner pays from their wallet to unlock the course. 0 = free.
    price_paise: int = Field(default=0, ge=0, le=100_000_000)
    cover_image_url: str | None = Field(default=None, max_length=500)
    level: CourseLevel = CourseLevel.beginner
    duration_minutes: int | None = Field(default=None, ge=0, le=100_000)
    outcomes: list[str] = Field(default_factory=list, max_length=20)
    #: Days of access one purchase buys. Blank means permanent access.
    access_days: int | None = Field(default=None, ge=1, le=3650)

    @model_validator(mode="after")
    def _clean(self) -> "CourseWrite":
        self.title = self.title.strip()
        self.category = self.category.strip()
        self.description = self.description.strip()
        self.outcomes = _clean_outcomes(self.outcomes)
        self.cover_image_url = (self.cover_image_url or "").strip() or None
        return self


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    category: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    is_published: bool | None = None
    price_paise: int | None = Field(default=None, ge=0, le=100_000_000)
    cover_image_url: str | None = Field(default=None, max_length=500)
    level: CourseLevel | None = None
    duration_minutes: int | None = Field(default=None, ge=0, le=100_000)
    outcomes: list[str] | None = Field(default=None, max_length=20)
    access_days: int | None = Field(default=None, ge=1, le=3650)

    def changes(self) -> dict:
        """Only the fields the console actually sent, cleaned for storage.

        `cover_image_url`, `duration_minutes` and `access_days` can be cleared by
        sending an empty value; the NOT NULL columns ignore an explicit null.
        """
        data = self.model_dump(exclude_unset=True)
        for field in _NOT_NULL_COURSE_FIELDS:
            if field in data and data[field] is None:
                data.pop(field)
        for field, value in list(data.items()):
            if isinstance(value, str):
                data[field] = value.strip()
        if "cover_image_url" in data:
            data["cover_image_url"] = data["cover_image_url"] or None
        if "outcomes" in data:
            data["outcomes"] = _clean_outcomes(data["outcomes"])
        return data


class TopicAdminOut(BaseModel):
    id: int
    course_id: int
    course_title: str
    title: str
    position: int
    video_url: str | None
    content: str
    task_count: int


class TopicWrite(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    content: str = ""
    video_url: str | None = Field(default=None, max_length=500)
    position: int = Field(default=0, ge=0)


class TopicUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    content: str | None = None
    video_url: str | None = Field(default=None, max_length=500)
    position: int | None = Field(default=None, ge=0)


class TopicReorderRequest(BaseModel):
    ordered_ids: list[int] = Field(min_length=1)


# ---------------------------------------------------------------------------
# Tasks / quiz builder
# ---------------------------------------------------------------------------


class QuizQuestionIn(BaseModel):
    """A quiz question as authored in the admin quiz builder."""

    id: str | None = None
    prompt: str = Field(min_length=1, max_length=1000)
    options: list[str] = Field(min_length=2, max_length=8)
    correct_index: int = Field(ge=0)
    points: int = Field(default=1, ge=1, le=100)

    @model_validator(mode="after")
    def _check(self) -> "QuizQuestionIn":
        self.options = [option.strip() for option in self.options]
        if any(not option for option in self.options):
            raise ValueError("Every option needs some text.")
        if self.correct_index >= len(self.options):
            raise ValueError("The correct answer must be one of the options.")
        return self


class QuizQuestionOut(BaseModel):
    id: str
    prompt: str
    options: list[str]
    correct_index: int
    points: int


class TaskAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic_id: int
    topic_title: str
    course_id: int
    course_title: str
    title: str
    type: TaskType
    pass_percent: int
    reward: int
    is_active: bool
    question_count: int
    reward_claim_count: int


class TaskWrite(BaseModel):
    topic_id: int
    title: str = Field(min_length=2, max_length=200)
    pass_percent: int = Field(default=70, ge=0, le=100)
    reward: int = Field(default=0, ge=0)
    is_active: bool = True
    questions: list[QuizQuestionIn] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check(self) -> "TaskWrite":
        self.title = self.title.strip()
        return self


class TaskUpdate(BaseModel):
    topic_id: int | None = None
    title: str | None = Field(default=None, min_length=2, max_length=200)
    pass_percent: int | None = Field(default=None, ge=0, le=100)
    reward: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    questions: list[QuizQuestionIn] | None = None


class TaskAdminDetail(TaskAdminOut):
    """A single task with its full question set, for the quiz builder."""

    questions: list[QuizQuestionOut]


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


class AdminUserOut(BaseModel):
    id: int
    name: str
    email: str
    is_admin: bool
    has_active_subscription: bool
    subscribed_until: datetime | None
    created_at: datetime
    wallet_balance_paise: int
    lifetime_earned_paise: int
    attempt_count: int
    passed_count: int


class AdminUserUpdate(BaseModel):
    is_admin: bool | None = None
    #: Add this many days to the subscription (extends rather than resets).
    grant_subscription_days: int | None = Field(default=None, ge=1, le=3650)
    #: Remove the subscription entirely.
    revoke_subscription: bool | None = None


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


class DayPoint(BaseModel):
    day: str
    revenue_paise: int
    rewards_paise: int
    signups: int = 0
    attempts: int = 0


class GrowthWindow(BaseModel):
    """One 30-day bucket: what came in and what people did."""

    revenue_paise: int
    rewards_paise: int
    attempts: int
    signups: int


class GrowthComparison(BaseModel):
    days: int
    current: GrowthWindow
    previous: GrowthWindow


class FunnelStep(BaseModel):
    label: str
    count: int


class TopCourseOut(BaseModel):
    id: int
    title: str
    category: str
    learners: int
    attempts: int
    passed: int
    rewards_paise: int


class TopLearnerOut(BaseModel):
    id: int
    name: str
    email: str
    rewards_paise: int
    attempts: int
    passed: int


class RecentAttemptOut(BaseModel):
    id: int
    user_name: str
    task_title: str
    course_title: str
    percent: int
    passed: bool
    created_at: datetime


class UnderstandingCount(BaseModel):
    """One bar of the "how was your understanding?" breakdown."""

    rating: str
    count: int


class ReportOverview(BaseModel):
    revenue_paise: int
    rewards_paid_paise: int
    rewards_today_paise: int
    reward_ratio_percent: float
    reward_ratio_warning: bool
    warning_threshold_percent: int
    rewards_enabled: bool
    total_users: int
    subscribed_users: int
    total_attempts: int
    passed_attempts: int
    pass_rate_percent: float
    course_count: int
    topic_count: int
    task_count: int
    active_task_count: int
    video_completions: int
    understanding_counts: list[UnderstandingCount]
    recent_transactions: list["RecentTransactionOut"]
    recent_attempts: list[RecentAttemptOut]
    funnel: list[FunnelStep]
    top_courses: list[TopCourseOut]
    top_learners: list[TopLearnerOut]
    growth: GrowthComparison
    active_learners_7d: int
    daily: list[DayPoint]


class RecentTransactionOut(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_email: str
    kind: str
    amount: int
    status: str
    note: str
    created_at: datetime


ReportOverview.model_rebuild()
