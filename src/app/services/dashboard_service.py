from datetime import date, datetime
from typing import Any


def _date(value: date | datetime) -> date:
    return value.date() if isinstance(value, datetime) else value


class DashboardService:
    def __init__(self, operations, passengers, financials, alerts):
        self.operations = operations
        self.passengers = passengers
        self.financials = financials
        self.alerts = alerts

    def overview(self, start_date: date, end_date: date) -> dict[str, Any]:
        operation_rows = self.operations.find_range(start_date, end_date)
        passenger_rows = self.passengers.find_range(start_date, end_date)
        financial_rows = self.financials.find_range(start_date, end_date)

        system_rows = [row for row in operation_rows if row.get("line_code") is None]
        total_rows = system_rows or operation_rows
        daily: dict[date, dict[str, Any]] = {}

        def point(day: date) -> dict[str, Any]:
            return daily.setdefault(
                day,
                {
                    "date": day,
                    "passengers": 0,
                    "scheduled_trips": 0,
                    "completed_trips": 0,
                    "total_km": 0.0,
                    "sales": 0.0,
                    "usage": 0.0,
                },
            )

        for row in total_rows:
            item = point(_date(row["date"]))
            item["scheduled_trips"] += row.get("scheduled_trips", 0)
            item["completed_trips"] += row.get("completed_trips", 0)
            item["total_km"] += row.get("productive_km", 0) + row.get("deadhead_km", 0)

        for row in passenger_rows:
            item = point(_date(row["date"]))
            item["passengers"] += (
                row.get("fare_gate", 0) + row.get("prepaid", 0) + row.get("non_paying", 0)
            )

        for row in financial_rows:
            item = point(_date(row["date"]))
            item["sales"] += row.get("sales", 0)
            item["usage"] += row.get("usage", 0)

        line_totals: dict[str, dict[str, Any]] = {}
        for row in operation_rows:
            line_code = row.get("line_code")
            if not line_code:
                continue
            line = line_totals.setdefault(
                line_code,
                {"line_code": line_code, "completed_trips": 0, "total_km": 0.0},
            )
            line["completed_trips"] += row.get("completed_trips", 0)
            line["total_km"] += row.get("productive_km", 0) + row.get("deadhead_km", 0)

        scheduled = sum(row.get("scheduled_trips", 0) for row in total_rows)
        completed = sum(row.get("completed_trips", 0) for row in total_rows)
        fare_gate = sum(row.get("fare_gate", 0) for row in passenger_rows)
        prepaid = sum(row.get("prepaid", 0) for row in passenger_rows)
        non_paying = sum(row.get("non_paying", 0) for row in passenger_rows)
        sales = sum(row.get("sales", 0) for row in financial_rows)
        usage = sum(row.get("usage", 0) for row in financial_rows)
        total_km = sum(
            row.get("productive_km", 0) + row.get("deadhead_km", 0) for row in total_rows
        )

        return {
            "start_date": start_date,
            "end_date": end_date,
            "totals": {
                "passengers": fare_gate + prepaid + non_paying,
                "paying_passengers": fare_gate + prepaid,
                "non_paying_passengers": non_paying,
                "scheduled_trips": scheduled,
                "completed_trips": completed,
                "missing_trips": max(scheduled - completed, 0),
                "total_km": round(total_km, 2),
                "completion_rate": round(completed / scheduled * 100, 2) if scheduled else 0,
                "sales": round(sales, 2),
                "usage": round(usage, 2),
                "circulating_credit": round(sales - usage, 2),
                "open_alerts": self.alerts.count_open(start_date, end_date),
            },
            "daily": [
                {**value, "total_km": round(value["total_km"], 2)}
                for _, value in sorted(daily.items())
            ],
            "top_lines": sorted(
                (
                    {**line, "total_km": round(line["total_km"], 2)}
                    for line in line_totals.values()
                ),
                key=lambda row: row["completed_trips"],
                reverse=True,
            )[:10],
        }
