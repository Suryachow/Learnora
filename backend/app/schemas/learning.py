"""Read models for the course catalogue.

Task payloads sent to the browser deliberately exclude `config`, so quiz answers
and coding test cases can never leak to the client.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from ..models import CourseLevel, TaskType
from .progress import TopicProgressOut


class TaskPublic(BaseModel):
    """What a learner may know about a task before attempting it."""

    id: int
    topic_id: int
    title: str
    type: TaskType
    pass_percent: int
    reward: int
    question_count: int


class TopicSummary(BaseModel):
    id: int
    title: str
    position: int
    has_video: bool
    task_count: int


class TopicDetail(BaseModel):
    id: int
    course_id: int
    course_title: str
    title: str
    content: str
    video_url: str | None
    position: int
    total_reward: int
    tasks: list[TaskPublic]
    #: A paid course the reader does not own: the material above is withheld.
    is_locked: bool = False
    #: False only for a paid course that has not been bought.
    has_course_access: bool = True
    #: Free courses still ask for a subscription before the assessments open.
    requires_subscription: bool = True
    course_price_paise: int = 0
    #: Only present when the request carried a valid token.
    progress: TopicProgressOut | None = None


class CourseSummary(BaseModel):
    id: int
    title: str
    category: str
    description: str
    price_paise: int = 0
    cover_image_url: str | None = None
    level: CourseLevel = CourseLevel.beginner
    duration_minutes: int | None = None
    outcomes: list[str] = Field(default_factory=list)
    #: Days one purchase buys; None means the purchase never expires.
    access_days: int | None = None
    topic_count: int
    task_count: int
    total_reward: int


class CourseDetail(CourseSummary):
    topics: list[TopicSummary]
    #: True for a free course, or once this reader has bought it.
    has_access: bool = True
    #: When the current purchase lapses; None means permanent access.
    access_expires_at: datetime | None = None


class CategorySummary(BaseModel):
    name: str
    course_count: int
