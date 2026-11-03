from collections import defaultdict
from datetime import date, datetime
from typing import Any


def _date(value: date | datetime) -> date:
    return value.date() if isinstance(value, datetime) else value


def _trip_totals(scheduled: int, completed: int) -> dict[str, int | float]:
    return {
        "scheduled": scheduled,
        "completed": completed,
        "missing": max(scheduled - completed, 0),
        "completion_rate": round(completed / scheduled * 100, 2) if scheduled else 0,
    }


class AnalyticsService:
    """Agrega os contratos consumidos pelas telas analíticas do Flutter."""

    def __init__(self, operations, passengers, financials, hourly_operations):
        self.operations = operations
        self.passengers = passengers
        self.financials = financials
        self.hourly_operations = hourly_operations

    def operation(self, start_date: date, end_date: date) -> dict[str, Any]:
        rows = self.operations.find_range(start_date, end_date)
        system_rows = [row for row in rows if not row.get("line_code")]
        total_rows = system_rows or rows

        def operation_values(items):
            scheduled = sum(item.get("scheduled_trips", 0) for item in items)
            completed = sum(item.get("completed_trips", 0) for item in items)
            productive = sum(item.get("productive_km", 0) for item in items)
            deadhead = sum(item.get("deadhead_km", 0) for item in items)
            return {
                **_trip_totals(scheduled, completed),
                "productive_km": round(productive, 2),
                "deadhead_km": round(deadhead, 2),
                "total_km": round(productive + deadhead, 2),
            }

        daily_groups: dict[date, list[dict]] = defaultdict(list)
        for row in total_rows:
            daily_groups[_date(row["date"])].append(row)

        line_groups: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            if row.get("line_code"):
                line_groups[str(row["line_code"])].append(row)

        band_fields = (
            ("morning", "Manhã", "morning_scheduled", "morning_completed"),
            ("afternoon", "Tarde", "afternoon_scheduled", "afternoon_completed"),
            ("night", "Noite", "night_scheduled", "night_completed"),
        )
        bands = []
        for key, label, scheduled_field, completed_field in band_fields:
            scheduled = sum(row.get(scheduled_field, 0) for row in total_rows)
            completed = sum(row.get(completed_field, 0) for row in total_rows)
            bands.append({"key": key, "label": label, **_trip_totals(scheduled, completed)})

        return {
            "start_date": start_date,
            "end_date": end_date,
            "totals": operation_values(total_rows),
            "daily": [
                {"date": day, **operation_values(items)}
                for day, items in sorted(daily_groups.items())
            ],
            "lines": sorted(
                [
                    {
                        "line_code": line,
                        "completed_trips": sum(
                            item.get("completed_trips", 0) for item in items
                        ),
                        "total_km": round(
                            sum(
                                item.get("productive_km", 0)
                                + item.get("deadhead_km", 0)
                                for item in items
                            ),
                            2,
                        ),
                    }
                    for line, items in line_groups.items()
                ],
                key=lambda item: item["completed_trips"],
                reverse=True,
            ),
            "time_bands": bands,
        }

    def passenger(self, start_date: date, end_date: date) -> dict[str, Any]:
        rows = self.passengers.find_range(start_date, end_date)
        daily = []
        for row in rows:
            fare_gate = row.get("fare_gate", 0)
            prepaid = row.get("prepaid", 0)
            non_paying = row.get("non_paying", 0)
            paying = fare_gate + prepaid
            daily.append(
                {
                    "date": _date(row["date"]),
                    "fare_gate": fare_gate,
                    "prepaid": prepaid,
                    "non_paying": non_paying,
                    "paying": paying,
                    "total": paying + non_paying,
                }
            )
        daily.sort(key=lambda item: item["date"])

        weekly_groups: dict[int, list[dict]] = defaultdict(list)
        for item in daily:
            week = (item["date"] - start_date).days // 7 + 1
            weekly_groups[week].append(item)
        weekly = []
        previous_average = None
        for week, items in sorted(weekly_groups.items()):
            total = sum(item["total"] for item in items)
            average = round(total / len(items), 2)
            change = (
                round(average / previous_average * 100 - 100, 2)
                if previous_average
                else None
            )
            weekly.append(
                {
                    "week": week,
                    "start_date": items[0]["date"],
                    "end_date": items[-1]["date"],
                    "total": total,
                    "daily_average": average,
                    "change_percentage": change,
                }
            )
            previous_average = average

        hourly_rows = self.hourly_operations.find_range(start_date, end_date)
        summary_rows = [row for row in hourly_rows if not row.get("line_code")]
        hourly_rows = summary_rows or hourly_rows
        hours: dict[int, dict[str, int]] = defaultdict(
            lambda: {"vehicles": 0, "trips": 0}
        )
        for row in hourly_rows:
            hour = int(row["hour"])
            hours[hour]["vehicles"] += row.get("vehicles", 0)
            hours[hour]["trips"] += row.get("trips", 0)

        fare_gate = sum(item["fare_gate"] for item in daily)
        prepaid = sum(item["prepaid"] for item in daily)
        non_paying = sum(item["non_paying"] for item in daily)
        total = fare_gate + prepaid + non_paying
        return {
            "start_date": start_date,
            "end_date": end_date,
            "totals": {
                "total": total,
                "paying": fare_gate + prepaid,
                "fare_gate": fare_gate,
                "prepaid": prepaid,
                "non_paying": non_paying,
                "daily_average": round(total / len(daily), 2) if daily else 0,
            },
            "daily": daily,
            "weekly": weekly,
            "hourly_supply": [
                {
                    "hour": hour,
                    "label": f"{hour}h",
                    "vehicles": values["vehicles"],
                    "trips": values["trips"],
                }
                for hour, values in sorted(hours.items(), key=lambda item: (item[0] - 4) % 24)
            ],
        }

    def financial(self, start_date: date, end_date: date) -> dict[str, Any]:
        rows = self.financials.find_range(start_date, end_date)
        passengers = self.passengers.find_range(start_date, end_date)
        daily = [
            {
                "date": _date(row["date"]),
                "sales": round(row.get("sales", 0), 2),
                "usage": round(row.get("usage", 0), 2),
                "circulating_credit": round(
                    row.get("sales", 0) - row.get("usage", 0), 2
                ),
            }
            for row in rows
        ]
        daily.sort(key=lambda item: item["date"])

        passenger_by_week: dict[int, int] = defaultdict(int)
        for row in passengers:
            week = (_date(row["date"]) - start_date).days // 7 + 1
            passenger_by_week[week] += (
                row.get("fare_gate", 0)
                + row.get("prepaid", 0)
                + row.get("non_paying", 0)
            )

        weekly_groups: dict[int, list[dict]] = defaultdict(list)
        monthly_groups: dict[tuple[int, int], list[dict]] = defaultdict(list)
        for item in daily:
            weekly_groups[(item["date"] - start_date).days // 7 + 1].append(item)
            monthly_groups[(item["date"].year, item["date"].month)].append(item)

        sales = sum(item["sales"] for item in daily)
        usage = sum(item["usage"] for item in daily)
        return {
            "start_date": start_date,
            "end_date": end_date,
            "totals": {
                "sales": round(sales, 2),
                "usage": round(usage, 2),
                "circulating_credit": round(sales - usage, 2),
                "usage_rate": round(usage / sales * 100, 2) if sales else 0,
                "daily_average_sales": round(sales / len(daily), 2) if daily else 0,
            },
            "daily": daily,
            "weekly": [
                {
                    "week": week,
                    "start_date": items[0]["date"],
                    "end_date": items[-1]["date"],
                    "sales": round(sum(item["sales"] for item in items), 2),
                    "usage": round(sum(item["usage"] for item in items), 2),
                    "passengers": passenger_by_week[week],
                }
                for week, items in sorted(weekly_groups.items())
            ],
            "monthly": [
                {
                    "year": year,
                    "month": month,
                    "label": f"{month:02d}/{year}",
                    "sales": round(sum(item["sales"] for item in items), 2),
                    "usage": round(sum(item["usage"] for item in items), 2),
                    "circulating_credit": round(
                        sum(item["sales"] - item["usage"] for item in items), 2
                    ),
                }
                for (year, month), items in sorted(monthly_groups.items())
            ],
        }
