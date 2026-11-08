from pydantic import Field

from src.app.models.common import DataSource, DocumentModel, ImportStatus


class ImportJob(DocumentModel):
    requested_by: str
    source: DataSource
    import_type: str
    file_name: str | None = None
    checksum_sha256: str | None = None
    dry_run: bool = False
    status: ImportStatus = ImportStatus.PROCESSING
    parsed: int = 0
    inserted_or_updated: int = 0
    counts: dict[str, int] = Field(default_factory=dict)
    error_message: str | None = None
