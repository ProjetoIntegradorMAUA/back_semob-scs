from datetime import date

from src.app.models.common import DataSource, DocumentModel


class Operation(DocumentModel):
    date: date
    line_code: str | None = None
    vehicles_operated: int = 0
    max_vehicles_in_service: int = 0
    scheduled_trips: int = 0
    completed_trips: int = 0
    productive_km: float = 0
    deadhead_km: float = 0
    source: DataSource = DataSource.MANUAL
