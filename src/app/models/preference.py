from src.app.models.common import DocumentModel


class UserPreference(DocumentModel):
    user_id: str
    default_period: str | None = None
    theme: str = "system"
    notify_critical_alerts: bool = True
    weekly_email_summary: bool = False
