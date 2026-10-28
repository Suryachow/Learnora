"""Read models for a learner's progress through a topic."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from ..models import Understanding


class TopicProgressOut(BaseModel):
    topic_id: int
    video_completed_at: datetime | None
    video_watched_seconds: int
    video_duration_seconds: int
    understanding: Understanding | None
    understanding_note: str
    understood_at: datetime | None
    #: What the lesson reward did when the video was completed. Only filled in
    #: by the video-complete response; reads leave it at the defaults.
    reward_granted: bool = False
    reward_paise: int = 0
    reward_reason: str = ""

    @property
    def video_completed(self) -> bool:
        return self.video_completed_at is not None

    @property
    def understood(self) -> bool:
        return self.understood_at is not None


class VideoCompleteRequest(BaseModel):
    """What the browser measured while the lesson played."""

    watched_seconds: int = Field(ge=0, le=60 * 60 * 6)
    duration_seconds: int = Field(ge=5, le=60 * 60 * 6)


class UnderstandingRequest(BaseModel):
    rating: Understanding
    note: str = Field(default="", max_length=1000)

    @field_validator("note")
    @classmethod
    def _trim(cls, value: str) -> str:
        return value.strip()


class ProgressSummaryOut(BaseModel):
    """Counts for the dashboard."""

    videos_completed: int
    videos_available: int
    understanding_recorded: int
