"""The single source of truth for tunable business settings.

Each knob is declared once, in `SETTINGS_SPECS`. A value stored in the
`app_settings` table wins; when nothing is stored the `.env` default applies.
Routers never read `config.settings` for these knobs - they call
`runtime_settings(db)` so an admin edit takes effect immediately.
"""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings as env_settings
from ..models import AppSetting


class SettingError(Exception):
    """Raised when a proposed setting value is not acceptable."""


@dataclass(frozen=True)
class SettingSpec:
    key: str
    label: str
    group: str
    kind: str  # "int" | "bool"
    default: Any
    description: str = ""
    unit: str = ""
    minimum: int | None = None
    maximum: int | None = None


SETTINGS_SPECS: tuple[SettingSpec, ...] = (
    SettingSpec(
        key="subscription_price_paise",
        label="Subscription price",
        group="Billing",
        kind="int",
        default=env_settings.subscription_price_paise,
        description="What one subscription term costs. Stored in paise (₹1 = 100).",
        unit="paise",
        minimum=0,
    ),
    SettingSpec(
        key="subscription_days",
        label="Subscription term",
        group="Billing",
        kind="int",
        default=env_settings.subscription_days,
        description="Days of access added by one successful payment.",
        unit="days",
        minimum=1,
        maximum=3650,
    ),
    SettingSpec(
        key="rewards_enabled",
        label="Rewards enabled",
        group="Rewards",
        kind="bool",
        default=env_settings.rewards_enabled,
        description="Master switch. When off, no reward is granted to anybody.",
    ),
    SettingSpec(
        key="reward_daily_limit_paise",
        label="Daily reward limit per user",
        group="Rewards",
        kind="int",
        default=env_settings.reward_daily_limit_paise,
        description="Most one learner can earn in a single day.",
        unit="paise",
        minimum=0,
    ),
    SettingSpec(
        key="reward_per_task_limit_paise",
        label="Maximum reward per task",
        group="Rewards",
        kind="int",
        default=env_settings.reward_per_task_limit_paise,
        description="A task may never pay more than this, whatever it is configured to.",
        unit="paise",
        minimum=0,
    ),
    SettingSpec(
        key="video_reward_paise",
        label="Video completion reward",
        group="Rewards",
        kind="int",
        default=env_settings.video_reward_paise,
        description=(
            "Paid once per lesson when its video is watched to the end. "
            "Set 0 to stop paying for video completion."
        ),
        unit="paise",
        minimum=0,
        maximum=100000,
    ),
    SettingSpec(
        key="reward_max_percent_of_revenue",
        label="Reward / revenue warning threshold",
        group="Rewards",
        kind="int",
        default=env_settings.reward_max_percent_of_revenue,
        description="The admin report warns when rewards exceed this share of revenue.",
        unit="%",
        minimum=0,
        maximum=100,
    ),
    SettingSpec(
        key="attempt_cooldown_seconds",
        label="Attempt cooldown",
        group="Assessment",
        kind="int",
        default=env_settings.attempt_cooldown_seconds,
        description="Minimum gap between two submissions on the same task.",
        unit="seconds",
        minimum=0,
        maximum=3600,
    ),
    SettingSpec(
        key="submission_rate_limit_per_minute",
        label="Submissions per minute",
        group="Assessment",
        kind="int",
        default=env_settings.submission_rate_limit_per_minute,
        description="Most submissions one learner may make in a minute.",
        unit="attempts",
        minimum=1,
        maximum=600,
    ),
)

_SPEC_BY_KEY: dict[str, SettingSpec] = {spec.key: spec for spec in SETTINGS_SPECS}


@dataclass(frozen=True)
class RuntimeSettings:
    """Typed, validated settings for one request."""

    subscription_price_paise: int
    subscription_days: int
    rewards_enabled: bool
    reward_daily_limit_paise: int
    reward_per_task_limit_paise: int
    video_reward_paise: int
    reward_max_percent_of_revenue: int
    attempt_cooldown_seconds: int
    submission_rate_limit_per_minute: int


def _as_bool(raw: Any) -> bool:
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        return bool(raw)
    if isinstance(raw, str):
        return raw.strip().lower() in {"1", "true", "yes", "on"}
    return bool(raw)


def _coerce(spec: SettingSpec, raw: Any, *, strict: bool) -> Any:
    """Turn a stored/submitted value into the spec's type.

    In `strict` mode (admin writes) out-of-range values raise; otherwise they
    are clamped so a bad row can never break a request.
    """
    if spec.kind == "bool":
        return _as_bool(raw)

    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise SettingError(f"{spec.label} must be a whole number.") from exc

    if spec.minimum is not None and value < spec.minimum:
        if strict:
            raise SettingError(f"{spec.label} cannot be less than {spec.minimum}.")
        value = spec.minimum
    if spec.maximum is not None and value > spec.maximum:
        if strict:
            raise SettingError(f"{spec.label} cannot be more than {spec.maximum}.")
        value = spec.maximum
    return value


def _overrides(db: Session) -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    for row in db.scalars(select(AppSetting)):
        spec = _SPEC_BY_KEY.get(row.key)
        if spec is None:
            continue  # a key we no longer recognise
        try:
            overrides[row.key] = _coerce(spec, row.value, strict=False)
        except SettingError:
            continue
    return overrides


def runtime_settings(db: Session) -> RuntimeSettings:
    """Effective settings: database overrides merged over the `.env` defaults."""
    merged = {spec.key: spec.default for spec in SETTINGS_SPECS}
    merged.update(_overrides(db))
    return RuntimeSettings(**merged)


def describe(db: Session) -> list[dict[str, Any]]:
    """Everything the admin settings screen needs, in declaration order."""
    overrides = _overrides(db)
    return [
        {
            "key": spec.key,
            "label": spec.label,
            "group": spec.group,
            "kind": spec.kind,
            "unit": spec.unit,
            "description": spec.description,
            "minimum": spec.minimum,
            "maximum": spec.maximum,
            "value": overrides.get(spec.key, spec.default),
            "default": spec.default,
            "is_overridden": spec.key in overrides,
        }
        for spec in SETTINGS_SPECS
    ]


def update_settings(
    db: Session, updates: dict[str, Any], *, updated_by: int | None
) -> RuntimeSettings:
    """Validate and persist a batch of changes, then return the new settings."""
    validated: dict[str, Any] = {}
    for key, raw in updates.items():
        spec = _SPEC_BY_KEY.get(key)
        if spec is None:
            raise SettingError(f"Unknown setting {key!r}.")
        validated[key] = _coerce(spec, raw, strict=True)

    for key, value in validated.items():
        row = db.get(AppSetting, key)
        if row is None:
            db.add(AppSetting(key=key, value=value, updated_by=updated_by))
        else:
            row.value = value
            row.updated_by = updated_by

    db.commit()
    return runtime_settings(db)


def reset_setting(db: Session, key: str, *, updated_by: int | None) -> RuntimeSettings:
    """Drop an override so the `.env` default applies again."""
    if key not in _SPEC_BY_KEY:
        raise SettingError(f"Unknown setting {key!r}.")
    row = db.get(AppSetting, key)
    if row is not None:
        db.delete(row)
        db.commit()
    return runtime_settings(db)
