from datetime import date

from src.app.models.common import DataSource, DocumentModel


class Financial(DocumentModel):
    date: date
    sales: float = 0
    usage: float = 0
    credits_transferred: float = 0
    system_balance: float | None = None
    source: DataSource = DataSource.MANUAL
