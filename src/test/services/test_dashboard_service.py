from datetime import date

from src.app.services.dashboard_service import DataCoverageService, DashboardService


class SeriesRepository:
    def __init__(self, rows):
        self.rows = rows

    def find_range(self, start_date, end_date):
        return self.rows


class AlertRepository:
    def count_open(self, start_date, end_date):
        return 2


class CoverageRepository:
    def __init__(self, records):
        self.records = records

    def coverage(self):
        return {
            "records": self.records,
            "start_date": date(2026, 8, 1) if self.records else None,
            "end_date": date(2026, 8, 31) if self.records else None,
            "last_updated": None,
        }


def test_dashboard_aggregates_all_domains_without_double_counting_lines():
    day = date(2026, 8, 1)
    operations = SeriesRepository(
        [
            {
                "date": day,
                "line_code": None,
                "scheduled_trips": 100,
                "completed_trips": 98,
                "productive_km": 700,
                "deadhead_km": 20,
            },
            {
                "date": day,
                "line_code": "01",
                "scheduled_trips": 40,
                "completed_trips": 39,
                "productive_km": 280,
                "deadhead_km": 8,
            },
        ]
    )
    passengers = SeriesRepository(
        [{"date": day, "fare_gate": 10, "prepaid": 5, "non_paying": 30}]
    )
    financials = SeriesRepository([{"date": day, "sales": 1000, "usage": 800}])

    result = DashboardService(
        operations, passengers, financials, AlertRepository()
    ).overview(day, day)

    assert result["totals"]["scheduled_trips"] == 100
    assert result["totals"]["passengers"] == 45
    assert result["totals"]["circulating_credit"] == 200
    assert result["totals"]["open_alerts"] == 2
    assert result["top_lines"][0]["line_code"] == "01"


def test_data_coverage_marks_dashboard_ready_only_with_every_dataset():
    ready = DataCoverageService(
        CoverageRepository(10),
        CoverageRepository(20),
        CoverageRepository(30),
        CoverageRepository(40),
    ).snapshot()
    incomplete = DataCoverageService(
        CoverageRepository(10),
        CoverageRepository(0),
        CoverageRepository(30),
        CoverageRepository(40),
    ).snapshot()

    assert ready["ready_for_dashboard"] is True
    assert ready["operations"]["records"] == 10
    assert ready["generated_at"].tzinfo is not None
    assert incomplete["ready_for_dashboard"] is False
