from datetime import datetime
from typing import Literal

from pydantic import Field

from src.app.schemas.common import ApiSchema


class HealthResponse(ApiSchema):
    status: Literal["ok"]
    service: str
    version: str
    checked_at: datetime


class ReadinessResponse(ApiSchema):
    status: Literal["ready", "degraded"]
    database: bool
    checked_at: datetime
    latency_ms: float = Field(ge=0)
