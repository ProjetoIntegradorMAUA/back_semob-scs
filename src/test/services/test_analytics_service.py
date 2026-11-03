from datetime import date, datetime

from src.app.services.analytics_service import AnalyticsService


class Series:
    def __init__(self, rows):
        self.rows = rows

    def find_range(self, start_date, end_date):
        return self.rows


def test_builds_all_frontend_analytics_contracts():
    operations = Series(
        [
            {
                "date": datetime(2026, 8, 1),
                "line_code": None,
                "scheduled_trips": 100,
                "completed_trips": 95,
                "productive_km": 900,
                "deadhead_km": 100,
                "morning_scheduled": 40,
                "morning_completed": 38,
                "afternoon_scheduled": 35,
                "afternoon_completed": 34,
                "night_scheduled": 25,
                "night_completed": 23,
            },
            {
                "date": date(2026, 8, 1),
                "line_code": "01",
                "completed_trips": 60,
                "productive_km": 600,
            },
            {
                "date": date(2026, 8, 1),
                "line_code": "02",
                "completed_trips": 35,
                "productive_km": 300,
            },
        ]
    )
    passengers = Series(
        [
            {
                "date": date(2026, 8, day),
                "fare_gate": 10 * day,
                "prepaid": 2,
                "non_paying": 3,
            }
            for day in range(1, 9)
        ]
    )
    financials = Series(
        [
            {"date": date(2026, 8, 1), "sales": 100, "usage": 80},
            {"date": date(2026, 9, 1), "sales": 200, "usage": 150},
        ]
    )
    hourly = Series(
        [
            {"date": date(2026, 8, 1), "hour": 4, "vehicles": 2, "trips": 3},
            {"date": date(2026, 8, 2), "hour": 4, "vehicles": 1, "trips": 2},
            {
                "date": date(2026, 8, 1),
                "hour": 4,
                "line_code": "01",
                "vehicles": 20,
                "trips": 30,
            },
        ]
    )
    service = AnalyticsService(operations, passengers, financials, hourly)

    operation = service.operation(date(2026, 8, 1), date(2026, 9, 30))
    passenger = service.passenger(date(2026, 8, 1), date(2026, 9, 30))
    financial = service.financial(date(2026, 8, 1), date(2026, 9, 30))

    assert operation["totals"]["completion_rate"] == 95
    assert operation["totals"]["total_km"] == 1000
    assert operation["lines"][0]["line_code"] == "01"
    assert operation["time_bands"][0]["completed"] == 38
    assert passenger["totals"]["total"] == 400
    assert len(passenger["weekly"]) == 2
    assert passenger["weekly"][1]["change_percentage"] is not None
    assert passenger["hourly_supply"][0]["trips"] == 5
    assert financial["totals"]["circulating_credit"] == 70
    assert financial["totals"]["usage_rate"] == 76.67
    assert len(financial["monthly"]) == 2
    assert financial["weekly"][0]["passengers"] > 0


def test_analytics_handles_line_only_and_empty_periods():
    operation_rows = [
        {
            "date": date(2026, 8, 1),
            "line_code": "01",
            "scheduled_trips": 0,
            "completed_trips": 2,
        }
    ]
    hourly_rows = [
        {
            "date": date(2026, 8, 1),
            "hour": 23,
            "line_code": "01",
            "vehicles": 1,
            "trips": 2,
        }
    ]
    service = AnalyticsService(Series(operation_rows), Series([]), Series([]), Series(hourly_rows))

    operation = service.operation(date(2026, 8, 1), date(2026, 8, 1))
    passenger = service.passenger(date(2026, 8, 1), date(2026, 8, 1))
    financial = service.financial(date(2026, 8, 1), date(2026, 8, 1))

    assert operation["totals"]["completion_rate"] == 0
    assert passenger["totals"]["daily_average"] == 0
    assert passenger["hourly_supply"][0]["hour"] == 23
    assert financial["totals"]["usage_rate"] == 0
    assert financial["totals"]["daily_average_sales"] == 0
