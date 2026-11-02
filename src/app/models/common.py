from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DocumentModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class DataSource(StrEnum):
    MANUAL = "manual"
    SMART_REPORT = "smart_report"
    SMART_DATA_API = "smart_data_api"


class AlertSeverity(StrEnum):
    LOW = "low"
    ATTENTION = "attention"
    CRITICAL = "critical"


class AlertStatus(StrEnum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"


class AlertRule(StrEnum):
    TRIP_COMPLETION_LOW = "trip_completion_low"
    DEADHEAD_KM_RATIO_HIGH = "deadhead_km_ratio_high"
    NEGATIVE_CIRCULATING_CREDIT = "negative_circulating_credit"


class ReportStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
