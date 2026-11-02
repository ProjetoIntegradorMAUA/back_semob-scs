from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database


def ensure_indexes(database: Database) -> None:
    """Cria índices idempotentes usados pelas consultas e pelos upserts."""

    database.users.create_index("email", unique=True)
    database.users.create_index("nome")
    database.operations.create_index(
        [("date", ASCENDING), ("line_code", ASCENDING)], unique=True
    )
    database.passengers.create_index("date", unique=True)
    database.financials.create_index("date", unique=True)
    database.alerts.create_index([("date", DESCENDING), ("status", ASCENDING)])
    database.alerts.create_index("severity")
    database.alerts.create_index(
        [("rule_code", ASCENDING), ("date", ASCENDING), ("line_code", ASCENDING)],
        unique=True,
        partialFilterExpression={"rule_code": {"$type": "string"}},
    )
    database.preferences.create_index("user_id", unique=True)
    database.report_jobs.create_index([("created_at", DESCENDING)])
