from datetime import datetime

from pydantic import Field

from src.app.schemas.common import ApiSchema


class PreferenceUpdate(ApiSchema):
    default_period: str | None = Field(default=None, max_length=30)
    notify_critical_alerts: bool = True
    weekly_email_summary: bool = False


class PreferenceResponse(PreferenceUpdate):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
