"""Runtime settings payloads for the admin console."""

from typing import Any

from pydantic import BaseModel


class SettingOut(BaseModel):
    key: str
    label: str
    group: str
    kind: str
    unit: str
    description: str
    minimum: int | None = None
    maximum: int | None = None
    value: Any
    default: Any
    is_overridden: bool


class SettingsUpdateRequest(BaseModel):
    """Only the keys present are changed; everything else keeps its value."""

    values: dict[str, Any]
