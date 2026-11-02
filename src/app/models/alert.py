from datetime import date

from src.app.models.common import AlertSeverity, AlertStatus, DocumentModel


class Alert(DocumentModel):
    date: date
    type: str
    description: str
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.OPEN
    line_code: str | None = None
    metric: str | None = None
    observed_value: float | None = None
    expected_value: float | None = None
