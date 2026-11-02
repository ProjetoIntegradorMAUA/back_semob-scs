from fastapi import APIRouter, Response, status

from src.app.core.config import get_settings
from src.app.db.session import ping_database

router = APIRouter(tags=["Saúde"])


@router.get("/health")
def health():
    settings = get_settings()
    return {"status": "ok", "service": settings.app_name, "version": settings.app_version}


@router.get("/ready")
def readiness(response: Response):
    database_ok = ping_database()
    if not database_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ready" if database_ok else "degraded", "database": database_ok}
