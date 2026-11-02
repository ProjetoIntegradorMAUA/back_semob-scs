from time import perf_counter

from fastapi import APIRouter, Response, status

from src.app.core.config import get_settings
from src.app.db.session import ping_database
from src.app.models.common import utc_now
from src.app.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter(tags=["Saúde"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Verifica se a API está em execução",
)
def health(response: Response):
    settings = get_settings()
    response.headers["Cache-Control"] = "no-store"
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "checked_at": utc_now(),
    }


def _readiness(response: Response) -> dict:
    started_at = perf_counter()
    database_ok = ping_database()
    if not database_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    response.headers["Cache-Control"] = "no-store"
    return {
        "status": "ready" if database_ok else "degraded",
        "database": database_ok,
        "checked_at": utc_now(),
        "latency_ms": round((perf_counter() - started_at) * 1000, 3),
    }


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    responses={503: {"description": "MongoDB indisponível"}},
    summary="Verifica se a API está pronta para receber tráfego",
)
def readiness(response: Response):
    return _readiness(response)


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    deprecated=True,
    summary="Alias legado da verificação de prontidão",
)
def legacy_readiness(response: Response):
    return _readiness(response)
