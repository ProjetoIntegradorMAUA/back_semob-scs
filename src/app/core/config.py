from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração carregada do ambiente e, opcionalmente, do arquivo .env."""

    app_name: str = "SEMOB-SCS API"
    app_version: str = "0.2.0"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_database: str = "semob_scs"
    mongo_connect_on_startup: bool = False
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=45, ge=5, le=1440)
    trip_completion_alert_threshold: float = Field(default=98.0, gt=0, le=100)
    trip_completion_critical_threshold: float = Field(default=90.0, gt=0, le=100)
    deadhead_km_alert_threshold: float = Field(default=8.0, ge=0, le=100)
    negative_credit_critical_amount: float = Field(default=10_000.0, ge=0)
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:8080"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_alert_thresholds(self):
        if self.trip_completion_critical_threshold > self.trip_completion_alert_threshold:
            raise ValueError(
                "TRIP_COMPLETION_CRITICAL_THRESHOLD deve ser menor ou igual a "
                "TRIP_COMPLETION_ALERT_THRESHOLD."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
