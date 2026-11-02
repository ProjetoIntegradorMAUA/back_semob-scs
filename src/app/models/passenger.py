from datetime import date

from src.app.models.common import DataSource, DocumentModel


class Passenger(DocumentModel):
    date: date
    fare_gate: int = 0
    prepaid: int = 0
    non_paying: int = 0
    source: DataSource = DataSource.MANUAL
