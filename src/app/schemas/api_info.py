from typing import Literal

from src.app.schemas.common import ApiSchema


class DocumentationLinks(ApiSchema):
    swagger: str
    redoc: str
    openapi: str


class HealthLinks(ApiSchema):
    liveness: str
    readiness: str


class ApiInfoResponse(ApiSchema):
    status: Literal["online"]
    service: str
    version: str
    api_prefix: str
    documentation: DocumentationLinks
    health: HealthLinks
