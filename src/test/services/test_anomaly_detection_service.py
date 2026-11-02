from datetime import date, datetime

import pytest
from pydantic import ValidationError

from src.app.core.config import Settings
from src.app.models.common import AlertRule, AlertSeverity
from src.app.services.anomaly_detection_service import AnomalyDetectionService


class SeriesRepository:
    def __init__(self, rows):
        self.rows = rows

    def find_range(self, start_date, end_date):
        return self.rows


class AlertRepository:
    def __init__(self, resolved=0):
        self.items = {}
        self.resolved = resolved
        self.active_keys = set()

    def upsert_generated(self, item):
        key = (item["rule_code"], item["date"], item.get("line_code"))
        created = key not in self.items
        self.items[key] = item
        return created

    def resolve_stale_generated(self, start_date, end_date, active_keys):
        self.active_keys = active_keys
        return self.resolved


def test_generates_idempotent_operational_and_financial_alerts():
    operations = SeriesRepository(
        [
            {
                "date": datetime(2026, 8, 1),
                "line_code": "01",
                "scheduled_trips": 100,
                "completed_trips": 95,
                "productive_km": 900,
                "deadhead_km": 100,
            },
            {
                "date": date(2026, 8, 2),
                "line_code": None,
                "scheduled_trips": 100,
                "completed_trips": 85,
                "productive_km": 990,
                "deadhead_km": 10,
            },
        ]
    )
    financials = SeriesRepository(
        [
            {"date": date(2026, 8, 1), "sales": 100, "usage": 150},
            {"date": date(2026, 8, 2), "sales": 0, "usage": 20_000},
        ]
    )
    alerts = AlertRepository()
    service = AnomalyDetectionService(operations, financials, alerts, Settings())

    first = service.generate(date(2026, 8, 1), date(2026, 8, 31))
    second = service.generate(date(2026, 8, 1), date(2026, 8, 31))

    assert first["candidates"] == 5
    assert first["created"] == 5
    assert first["updated"] == 0
    assert second["created"] == 0
    assert second["updated"] == 5
    assert first["by_rule"] == {
        AlertRule.TRIP_COMPLETION_LOW.value: 2,
        AlertRule.DEADHEAD_KM_RATIO_HIGH.value: 1,
        AlertRule.NEGATIVE_CIRCULATING_CREDIT.value: 2,
    }
    severities = {item["severity"] for item in alerts.items.values()}
    assert severities == {AlertSeverity.ATTENTION.value, AlertSeverity.CRITICAL.value}
    assert len(alerts.active_keys) == 5


def test_resolves_stale_alerts_when_anomalies_disappear():
    alerts = AlertRepository(resolved=2)
    service = AnomalyDetectionService(
        SeriesRepository(
            [
                {
                    "date": date(2026, 8, 1),
                    "scheduled_trips": 0,
                    "completed_trips": 0,
                    "productive_km": 0,
                    "deadhead_km": 0,
                }
            ]
        ),
        SeriesRepository(
            [{"date": date(2026, 8, 1), "sales": 100, "usage": 90}]
        ),
        alerts,
        Settings(),
    )

    result = service.generate(date(2026, 8, 1), date(2026, 8, 31))

    assert result["candidates"] == 0
    assert result["evaluated_operations"] == 1
    assert result["evaluated_financials"] == 1
    assert result["resolved"] == 2
    assert alerts.active_keys == set()


def test_rejects_inconsistent_completion_thresholds():
    with pytest.raises(ValidationError):
        Settings(
            trip_completion_alert_threshold=90,
            trip_completion_critical_threshold=95,
        )
