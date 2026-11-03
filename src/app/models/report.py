from datetime import date

from src.app.models.common import DocumentModel, ReportStatus


class ReportJob(DocumentModel):
    requested_by: str
    report_type: str
    format: str
    start_date: date
    end_date: date
    status: ReportStatus = ReportStatus.PENDING
    file_url: str | None = None
    file_name: str | None = None
    content_type: str | None = None
    error_message: str | None = None
