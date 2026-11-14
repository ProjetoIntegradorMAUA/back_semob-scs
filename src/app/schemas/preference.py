from datetime import datetime
from enum import StrEnum

from pydantic import Field, model_validator

from src.app.schemas.common import ApiSchema


class ThemePreference(StrEnum):
    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"


class PreferenceSettings(ApiSchema):
    default_period: str | None = Field(default=None, max_length=30)
    theme: ThemePreference = ThemePreference.SYSTEM
    notify_critical_alerts: bool = True
    weekly_email_summary: bool = False


class PreferenceUpdate(ApiSchema):
    default_period: str | None = Field(default=None, max_length=30)
    theme: ThemePreference | None = None
    notify_critical_alerts: bool | None = None
    weekly_email_summary: bool | None = None

    @model_validator(mode="after")
    def validate_non_empty(self):
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar.")
        return self


class PreferenceResponse(PreferenceSettings):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
