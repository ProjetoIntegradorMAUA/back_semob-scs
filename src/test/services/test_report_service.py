from datetime import date, datetime

from openpyxl import load_workbook

from src.app.models.common import DataSource
from src.app.schemas.report import ReportFormat, ReportType
from src.app.services.report_service import CONTENT_TYPES, ReportService


class Series:
    def __init__(self, rows):
        self.rows = rows

    def find_range(self, start_date, end_date):
        return self.rows


class Alerts(Series):
    def count_open(self, start_date, end_date):
        return len(self.rows)


def _service(tmp_path):
    operations = Series(
        [
            {
                "date": datetime(2026, 8, 1),
                "line_code": None,
                "scheduled_trips": 10,
                "completed_trips": 9,
                "productive_km": 100,
                "deadhead_km": 5,
                "source": DataSource.SMART_REPORT,
            }
        ]
    )
    passengers = Series(
        [{"date": date(2026, 8, 1), "fare_gate": 10, "prepaid": 2, "non_paying": 3}]
    )
    financials = Series([{"date": date(2026, 8, 1), "sales": 100, "usage": 80}])
    alerts = Alerts(
        [
            {
                "date": date(2026, 8, 1),
                "type": "Teste",
                "description": "Alerta de teste",
                "severity": "low",
            }
        ]
    )
    return ReportService(operations, passengers, financials, alerts, str(tmp_path))


def test_generates_csv_xlsx_and_pdf_files(tmp_path):
    service = _service(tmp_path)

    csv_result = service.generate(
        "csv-id",
        ReportType.OPERATIONS,
        ReportFormat.CSV,
        date(2026, 8, 1),
        date(2026, 8, 31),
    )
    xlsx_result = service.generate(
        "xlsx-id",
        ReportType.PASSENGERS,
        ReportFormat.XLSX,
        date(2026, 8, 1),
        date(2026, 8, 31),
    )
    pdf_result = service.generate(
        "pdf-id",
        ReportType.FINANCIALS,
        ReportFormat.PDF,
        date(2026, 8, 1),
        date(2026, 8, 31),
    )

    csv_content = service.path(csv_result["file_name"]).read_bytes()
    assert csv_content.startswith(b"\xef\xbb\xbf")
    assert b"scheduled_trips" in csv_content
    workbook = load_workbook(service.path(xlsx_result["file_name"]))
    assert workbook.active["A1"].value == "date"
    assert service.path(pdf_result["file_name"]).read_bytes().startswith(b"%PDF")
    assert csv_result["content_type"] == CONTENT_TYPES[ReportFormat.CSV]


def test_generates_alert_and_consolidated_reports_and_empty_sheet(tmp_path):
    service = _service(tmp_path)
    alert_result = service.generate(
        "alert-id",
        ReportType.ALERTS,
        ReportFormat.CSV,
        date(2026, 8, 1),
        date(2026, 8, 31),
    )
    consolidated = service.generate(
        "all-id",
        ReportType.CONSOLIDATED,
        ReportFormat.XLSX,
        date(2026, 8, 1),
        date(2026, 8, 31),
    )
    empty = ReportService(Series([]), Series([]), Series([]), Alerts([]), str(tmp_path))
    empty_result = empty.generate(
        "empty-id",
        ReportType.OPERATIONS,
        ReportFormat.CSV,
        date(2026, 8, 1),
        date(2026, 8, 31),
    )

    assert b"Alerta de teste" in service.path(alert_result["file_name"]).read_bytes()
    workbook = load_workbook(service.path(consolidated["file_name"]))
    assert workbook.active.max_row == 2
    assert b"sem_dados" in empty.path(empty_result["file_name"]).read_bytes()
