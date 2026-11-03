import csv
from datetime import date, datetime
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.app.schemas.report import ReportFormat, ReportType
from src.app.services.dashboard_service import DashboardService


CONTENT_TYPES = {
    ReportFormat.CSV: "text/csv; charset=utf-8",
    ReportFormat.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ReportFormat.PDF: "application/pdf",
}


def _plain(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return value


class ReportService:
    def __init__(
        self,
        operations,
        passengers,
        financials,
        alerts,
        output_dir: str,
    ):
        self.operations = operations
        self.passengers = passengers
        self.financials = financials
        self.alerts = alerts
        self.output_dir = Path(output_dir).resolve()

    def generate(
        self,
        report_id: str,
        report_type: ReportType,
        report_format: ReportFormat,
        start_date: date,
        end_date: date,
    ) -> dict[str, str]:
        title, rows = self._rows(report_type, start_date, end_date)
        normalized = [
            {key: _plain(value) for key, value in row.items() if key != "senha_hash"}
            for row in rows
        ]
        content = {
            ReportFormat.CSV: self._csv,
            ReportFormat.XLSX: self._xlsx,
            ReportFormat.PDF: lambda values: self._pdf(title, values),
        }[report_format](normalized)
        file_name = (
            f"{report_type.value}-{start_date.isoformat()}-{end_date.isoformat()}-"
            f"{report_id}.{report_format.value}"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / file_name).write_bytes(content)
        return {
            "file_name": file_name,
            "content_type": CONTENT_TYPES[report_format],
        }

    def path(self, file_name: str) -> Path:
        safe_name = Path(file_name).name
        path = (self.output_dir / safe_name).resolve()
        if path.parent != self.output_dir:
            raise ValueError("Caminho de relatório inválido.")
        return path

    def _rows(
        self, report_type: ReportType, start_date: date, end_date: date
    ) -> tuple[str, list[dict[str, Any]]]:
        if report_type == ReportType.OPERATIONS:
            return "Operação da Frota", self.operations.find_range(start_date, end_date)
        if report_type == ReportType.PASSENGERS:
            return "Análise de Passageiros", self.passengers.find_range(start_date, end_date)
        if report_type == ReportType.FINANCIALS:
            return "Indicadores Financeiros", self.financials.find_range(start_date, end_date)
        if report_type == ReportType.ALERTS:
            return "Alertas Operacionais", self.alerts.find_range(start_date, end_date)

        overview = DashboardService(
            self.operations, self.passengers, self.financials, self.alerts
        ).overview(start_date, end_date)
        return "Consolidado SEMOB-SCS", overview["daily"]

    @staticmethod
    def _columns(rows: list[dict[str, Any]]) -> list[str]:
        columns: list[str] = []
        for row in rows:
            for key in row:
                if key not in columns:
                    columns.append(key)
        return columns or ["sem_dados"]

    def _csv(self, rows: list[dict[str, Any]]) -> bytes:
        columns = self._columns(rows)
        stream = StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=columns, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
        return stream.getvalue().encode("utf-8-sig")

    def _xlsx(self, rows: list[dict[str, Any]]) -> bytes:
        columns = self._columns(rows)
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "SEMOB-SCS"
        sheet.append(columns)
        for cell in sheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="273469")
        for row in rows:
            sheet.append([row.get(column) for column in columns])
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        for column in sheet.columns:
            width = min(max(len(str(cell.value or "")) for cell in column) + 2, 45)
            sheet.column_dimensions[column[0].column_letter].width = width
        stream = BytesIO()
        workbook.save(stream)
        return stream.getvalue()

    def _pdf(self, title: str, rows: list[dict[str, Any]]) -> bytes:
        columns = self._columns(rows)[:10]
        stream = BytesIO()
        document = SimpleDocTemplate(
            stream,
            pagesize=landscape(A4),
            leftMargin=24,
            rightMargin=24,
            topMargin=24,
            bottomMargin=24,
        )
        styles = getSampleStyleSheet()
        data = [columns]
        data.extend(
            [[str(row.get(column, ""))[:60] for column in columns] for row in rows[:1000]]
        )
        table = Table(data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#273469")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F6FA")]),
                ]
            )
        )
        document.build(
            [Paragraph(title, styles["Title"]), Spacer(1, 12), table]
        )
        return stream.getvalue()
