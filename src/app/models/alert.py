from datetime import date

from src.app.models.common import AlertRule, AlertSeverity, AlertStatus, DocumentModel


class Alert(DocumentModel):
    date: date
    type: str
    description: str
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.OPEN
    line_code: str | None = None
    rule_code: AlertRule | None = None
    metric: str | None = None
    observed_value: float | None = None
    expected_value: float | None = None
