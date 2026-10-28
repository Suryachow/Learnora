"""Application settings loaded from environment variables / `.env`."""

from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent

DEV_JWT_SECRET = "change-me-in-production-please-use-a-long-random-value"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Learnora API"
    env: str = "dev"

    # Required on purpose. A silent fallback here is how a deployment ends up
    # writing to a throwaway SQLite file instead of the real PostgreSQL database.
    database_url: str

    jwt_secret: str = DEV_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    subscription_price_paise: int = 14900
    subscription_days: int = 30

    rewards_enabled: bool = True
    reward_daily_limit_paise: int = 50000
    reward_per_task_limit_paise: int = 20000
    reward_max_percent_of_revenue: int = 50
    #: Paid once per lesson when its video is watched to the end. 0 turns it off.
    video_reward_paise: int = 500
    attempt_cooldown_seconds: int = 10
    submission_rate_limit_per_minute: int = 20

    # ---- Quiz writing (optional) --------------------------------------------
    #: When set, `scripts/generate_quizzes.py` can write quizzes from lesson notes.
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    groq_base_url: str = "https://api.groq.com/openai/v1"
    quiz_questions_per_topic: int = 5
    quiz_generation_timeout_seconds: float = 45.0

    payment_provider: str = "mock"
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    @property
    def is_prod(self) -> bool:
        return self.env.lower() in {"prod", "production"}

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def groq_configured(self) -> bool:
        """True when a Groq key is present, so quiz writing can actually run."""
        return bool(self.groq_api_key.strip())

    @model_validator(mode="after")
    def _guard_production_secrets(self) -> "Settings":
        if self.is_prod and self.jwt_secret == DEV_JWT_SECRET:
            raise ValueError("JWT_SECRET must be set to a strong unique value when ENV=prod")
        return self

    @model_validator(mode="after")
    def _guard_ephemeral_database(self) -> "Settings":
        """Refuse a file database outside tests so real data always lands in PostgreSQL."""
        if self.database_url.startswith("sqlite") and self.env.lower() != "test":
            raise ValueError(
                "SQLite is only allowed when ENV=test. Set DATABASE_URL to the PostgreSQL "
                "connection string (postgresql+psycopg://...) for dev and prod."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
