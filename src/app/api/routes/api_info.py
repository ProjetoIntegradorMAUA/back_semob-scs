from fastapi import APIRouter

from src.app.core.config import get_settings
from src.app.schemas.api_info import ApiInfoResponse

router = APIRouter(tags=["Informações"])


@router.get(
    "/",
    response_model=ApiInfoResponse,
    summary="Apresenta a API e seus links principais",
)
def api_info():
    settings = get_settings()
    return {
        "status": "online",
        "service": settings.app_name,
        "version": settings.app_version,
        "api_prefix": settings.api_v1_prefix,
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        },
        "health": {
            "liveness": "/health",
            "readiness": "/health/ready",
        },
    }
