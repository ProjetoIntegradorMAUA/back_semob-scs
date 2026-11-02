from collections import Counter
from datetime import date, datetime
from typing import Any

from src.app.core.config import Settings
from src.app.models.common import AlertRule, AlertSeverity


def _date(value: date | datetime) -> date:
    return value.date() if isinstance(value, datetime) else value


class AnomalyDetectionService:
    """Aplica regras determinísticas aos dados consolidados da operação."""

    def __init__(self, operations, financials, alerts, settings: Settings):
        self.operations = operations
        self.financials = financials
        self.alerts = alerts
        self.settings = settings

    def generate(self, start_date: date, end_date: date) -> dict[str, Any]:
        operation_rows = self.operations.find_range(start_date, end_date)
        financial_rows = self.financials.find_range(start_date, end_date)
        candidates: list[dict[str, Any]] = []

        for row in operation_rows:
            candidates.extend(self._operation_alerts(row))
        for row in financial_rows:
            alert = self._financial_alert(row)
            if alert:
                candidates.append(alert)

        created = 0
        active_keys: set[tuple[str, str, str]] = set()
        for candidate in candidates:
            if self.alerts.upsert_generated(candidate):
                created += 1
            active_keys.add(
                (
                    str(candidate["rule_code"]),
                    candidate["date"].isoformat(),
                    candidate.get("line_code") or "",
                )
            )

        resolved = self.alerts.resolve_stale_generated(
            start_date, end_date, active_keys
        )
        by_rule = Counter(str(item["rule_code"]) for item in candidates)
        return {
            "start_date": start_date,
            "end_date": end_date,
            "evaluated_operations": len(operation_rows),
            "evaluated_financials": len(financial_rows),
            "candidates": len(candidates),
            "created": created,
            "updated": len(candidates) - created,
            "resolved": resolved,
            "by_rule": dict(by_rule),
        }

    def _operation_alerts(self, row: dict[str, Any]) -> list[dict[str, Any]]:
        alerts = []
        day = _date(row["date"])
        line_code = row.get("line_code")
        line_label = f" da linha {line_code}" if line_code else " do sistema"
        scheduled = row.get("scheduled_trips", 0)
        completed = row.get("completed_trips", 0)

        if scheduled > 0:
            completion_rate = completed / scheduled * 100
            if completion_rate < self.settings.trip_completion_alert_threshold:
                severity = (
                    AlertSeverity.CRITICAL
                    if completion_rate < self.settings.trip_completion_critical_threshold
                    else AlertSeverity.ATTENTION
                )
                alerts.append(
                    {
                        "date": day,
                        "type": "Baixo cumprimento de viagens",
                        "description": (
                            f"O cumprimento{line_label} foi de {completion_rate:.2f}%, "
                            f"abaixo do limite de "
                            f"{self.settings.trip_completion_alert_threshold:.2f}%."
                        ),
                        "severity": severity.value,
                        "line_code": line_code,
                        "rule_code": AlertRule.TRIP_COMPLETION_LOW.value,
                        "metric": "completion_rate",
                        "observed_value": round(completion_rate, 2),
                        "expected_value": self.settings.trip_completion_alert_threshold,
                    }
                )

        productive_km = row.get("productive_km", 0)
        deadhead_km = row.get("deadhead_km", 0)
        total_km = productive_km + deadhead_km
        if total_km > 0:
            deadhead_ratio = deadhead_km / total_km * 100
            if deadhead_ratio > self.settings.deadhead_km_alert_threshold:
                severity = (
                    AlertSeverity.CRITICAL
                    if deadhead_ratio >= self.settings.deadhead_km_alert_threshold * 2
                    else AlertSeverity.ATTENTION
                )
                alerts.append(
                    {
                        "date": day,
                        "type": "Quilometragem improdutiva elevada",
                        "description": (
                            f"A quilometragem improdutiva{line_label} representou "
                            f"{deadhead_ratio:.2f}% do total, acima do limite de "
                            f"{self.settings.deadhead_km_alert_threshold:.2f}%."
                        ),
                        "severity": severity.value,
                        "line_code": line_code,
                        "rule_code": AlertRule.DEADHEAD_KM_RATIO_HIGH.value,
                        "metric": "deadhead_km_ratio",
                        "observed_value": round(deadhead_ratio, 2),
                        "expected_value": self.settings.deadhead_km_alert_threshold,
                    }
                )
        return alerts

    def _financial_alert(self, row: dict[str, Any]) -> dict[str, Any] | None:
        circulating_credit = row.get("sales", 0) - row.get("usage", 0)
        if circulating_credit >= 0:
            return None
        severity = (
            AlertSeverity.CRITICAL
            if abs(circulating_credit) >= self.settings.negative_credit_critical_amount
            else AlertSeverity.ATTENTION
        )
        return {
            "date": _date(row["date"]),
            "type": "Crédito circulante negativo",
            "description": (
                f"A utilização superou as vendas em R$ {abs(circulating_credit):.2f}."
            ),
            "severity": severity.value,
            "line_code": None,
            "rule_code": AlertRule.NEGATIVE_CIRCULATING_CREDIT.value,
            "metric": "circulating_credit",
            "observed_value": round(circulating_credit, 2),
            "expected_value": 0,
        }
