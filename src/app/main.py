from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.api.routes.alerts import router as alerts_router
from src.app.api.routes.auth import router as auth_router
from src.app.api.routes.dashboard import router as dashboard_router
from src.app.api.routes.financials import router as financials_router
from src.app.api.routes.health import router as health_router
from src.app.api.routes.imports import router as imports_router
from src.app.api.routes.operations import router as operations_router
from src.app.api.routes.passengers import router as passengers_router
from src.app.api.routes.preferences import router as preferences_router
from src.app.api.routes.reports import router as reports_router
from src.app.api.routes.user import router as user_router
from src.app.core.config import get_settings
from src.app.db.indexes import ensure_indexes
from src.app.db.session import close_database, get_database

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.mongo_connect_on_startup:
        ensure_indexes(get_database())
    yield
    close_database()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API para consolidação e análise da operação do transporte municipal de São Caetano do Sul.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
for router in (
    auth_router,
    user_router,
    operations_router,
    passengers_router,
    financials_router,
    alerts_router,
    dashboard_router,
    imports_router,
    preferences_router,
    reports_router,
):
    app.include_router(router, prefix=settings.api_v1_prefix)


@app.get("/teste", deprecated=True)
def get_rota_teste():
    return {"mensagem": "Teste Funcionando"}
