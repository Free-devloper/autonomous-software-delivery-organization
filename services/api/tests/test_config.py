from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from autonomous_sdo_api.config import Environment, Settings

pytestmark = pytest.mark.unit


def test_settings_accept_explicit_benign_runtime_values() -> None:
    settings = Settings(
        service_name="api-staging",
        environment=Environment.STAGING,
        log_level="WARNING",
        request_timeout_seconds=120,
    )

    assert settings.service_name == "api-staging"
    assert settings.environment is Environment.STAGING
    assert settings.request_timeout_seconds == 120


def test_settings_accept_an_async_postgresql_database_url_without_exposing_it() -> None:
    settings = Settings.model_validate(
        {"database_url": "postgresql+asyncpg://app:password@localhost:5432/asdo"}
    )

    assert settings.database_url is not None
    assert "password" not in str(settings.database_url)
    assert settings.database_url.get_secret_value().endswith("/asdo")


@pytest.mark.parametrize("environment", [Environment.LOCAL, Environment.CI, Environment.DR])
def test_settings_accept_required_operational_environments(environment: Environment) -> None:
    assert Settings(environment=environment).environment is environment


def test_example_api_environment_values_are_valid() -> None:
    example_path = Path(__file__).resolve().parents[3] / ".env.example"
    values = {
        key.removeprefix("ASDO_API_").lower(): value
        for key, value in (
            line.split("=", maxsplit=1)
            for line in example_path.read_text().splitlines()
            if line.startswith("ASDO_API_")
        )
    }

    assert Settings.model_validate(values).environment is Environment.LOCAL


@pytest.mark.parametrize(
    ("values", "field_name"),
    [
        ({"environment": "preview"}, "environment"),
        ({"service_name": "API"}, "service_name"),
        ({"request_timeout_seconds": 0}, "request_timeout_seconds"),
        ({"database_url": "postgresql://localhost/asdo"}, "database_url"),
        ({"oidc_issuer": "https://idp.example.test"}, "oidc_"),
        ({"oidc_jwks": {"keys": "not-a-list"}}, "oidc_"),
        ({"unexpected_setting": "rejected"}, "unexpected_setting"),
    ],
)
def test_settings_reject_invalid_or_extra_values(
    values: dict[str, object], field_name: str
) -> None:
    with pytest.raises(ValidationError) as error:
        Settings.model_validate(values)

    assert field_name in str(error.value)
