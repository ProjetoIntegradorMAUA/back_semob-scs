from datetime import date

from src.app.models.common import DataSource, DocumentModel


class HourlyOperation(DocumentModel):
    date: date
    hour: int
    line_code: str | None = None
    vehicles: int = 0
    trips: int = 0
    source: DataSource = DataSource.MANUAL
