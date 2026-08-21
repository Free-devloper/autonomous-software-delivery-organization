"""Strict configuration for benign API process settings."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from typing import Annotated, Any, Literal
from urllib.parse import urlparse

from pydantic import Field, SecretStr, StringConstraints, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ServiceName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=3,
        max_length=63,
        pattern=r"^[a-z][a-z0-9-]*$",
    ),
]


class Environment(StrEnum):
    """Named deployment environments supported by the API process."""

    DEVELOPMENT = "development"
    LOCAL = "local"
    CI = "ci"
    DR = "dr"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Validated API settings, retaining connection credentials as secret values."""

    model_config = SettingsConfigDict(
        env_prefix="ASDO_API_",
        extra="forbid",
        case_sensitive=False,
        validate_default=True,
    )

    service_name: ServiceName = "autonomous-sdo-api"
    environment: Environment = Environment.DEVELOPMENT
    api_v1_prefix: Literal["/api/v1"] = "/api/v1"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    request_timeout_seconds: Annotated[int, Field(ge=1, le=300)] = 30
    database_url: SecretStr | None = None
    service_version: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = (
        "0.1.0"
    )
    telemetry_enabled: bool = True
    metrics_enabled: bool = True
    otlp_endpoint: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] | None = (
        None
    )
    oidc_issuer: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] | None = (
        None
    )
    oidc_audience: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] | None = (
        None
    )
    oidc_jwks: dict[str, Any] | None = None
    oidc_organization_claim: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=63),
    ] = "asdo_organizations"

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: SecretStr | None) -> SecretStr | None:
        """Accept only an async PostgreSQL URL when database access is configured."""
        if value is None:
            return None
        parsed = urlparse(value.get_secret_value())
        if parsed.scheme != "postgresql+asyncpg" or not parsed.hostname or parsed.path in {"", "/"}:
            raise ValueError("database_url must be a postgresql+asyncpg URL with host and database")
        return value

    @field_validator("otlp_endpoint")
    @classmethod
    def validate_otlp_endpoint(cls, value: str | None) -> str | None:
        if value is None:
            return None
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("otlp_endpoint must be an HTTP(S) URL with a host")
        if parsed.username or parsed.password:
            raise ValueError("otlp_endpoint must not contain credentials")
        return value.rstrip("/")

    @model_validator(mode="after")
    def validate_oidc_settings(self) -> Settings:
        oidc_values = [self.oidc_issuer, self.oidc_audience, self.oidc_jwks]
        if any(value is not None for value in oidc_values) and not all(
            value is not None for value in oidc_values
        ):
            raise ValueError("oidc_issuer, oidc_audience and oidc_jwks must be configured together")
        if self.oidc_jwks is not None and not isinstance(self.oidc_jwks.get("keys"), list):
            raise ValueError("oidc_jwks must be a JWKS object containing a keys list")
        return self

    @property
    def oidc_configured(self) -> bool:
        return (
            self.oidc_issuer is not None
            and self.oidc_audience is not None
            and self.oidc_jwks is not None
        )


@lru_cache
def get_settings() -> Settings:
    """Construct and cache process settings after Pydantic validation."""
    return Settings()
