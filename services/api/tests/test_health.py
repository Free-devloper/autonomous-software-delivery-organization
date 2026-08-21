from __future__ import annotations

import asyncio
import json
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from pydantic import SecretStr

import autonomous_sdo_api.app as app_module
from autonomous_sdo_api.app import create_app
from autonomous_sdo_api.config import Settings
from autonomous_sdo_api.schemas import HealthLiveResponse

pytestmark = pytest.mark.unit


def _jwks() -> dict[str, object]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(private_key.public_key()))
    jwk.update({"kid": "ready-key", "alg": "RS256", "use": "sig"})
    return {"keys": [jwk]}


async def _successful_ping() -> None:
    return None


async def _never_finishes_ping() -> None:
    await asyncio.Event().wait()


def test_live_health_uses_the_versioned_route_and_stable_contract() -> None:
    app = create_app(Settings(service_name="api-test"))

    with TestClient(app) as client:
        response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "status": "ok",
        "service": "api-test",
        "api_version": "v1",
    }
    assert HealthLiveResponse.model_validate(response.json()).model_dump() == response.json()


def test_ready_health_fails_closed_without_required_dependencies() -> None:
    app = create_app(Settings(service_name="api-test"))

    with TestClient(app) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == {"status": "unready", "missing": ["database", "oidc"]}


def test_ready_health_fails_closed_for_unreachable_database_and_empty_jwks() -> None:
    app = create_app(
        Settings(
            service_name="api-test",
            database_url=SecretStr("postgresql+asyncpg://asdo_app:password@127.0.0.1:1/asdo"),
            oidc_issuer="https://idp.example.test/realms/asdo",
            oidc_audience="asdo-api",
            oidc_jwks={"keys": []},
        )
    )

    with TestClient(app) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == {"status": "unready", "missing": ["database", "oidc"]}


def test_ready_health_succeeds_when_database_ping_and_oidc_key_are_usable() -> None:
    app = create_app(
        Settings(
            service_name="api-test",
            database_url=SecretStr("postgresql+asyncpg://asdo_app:password@127.0.0.1:1/asdo"),
            oidc_issuer="https://idp.example.test/realms/asdo",
            oidc_audience="asdo-api",
            oidc_jwks=_jwks(),
        )
    )
    app.state.tenant_session_factory.ping = _successful_ping

    with TestClient(app) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "api-test",
        "api_version": "v1",
    }


def test_ready_health_database_check_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    app = create_app(
        Settings(
            service_name="api-test",
            database_url=SecretStr("postgresql+asyncpg://asdo_app:password@127.0.0.1:1/asdo"),
            oidc_issuer="https://idp.example.test/realms/asdo",
            oidc_audience="asdo-api",
            oidc_jwks=_jwks(),
        )
    )
    app.state.tenant_session_factory.ping = _never_finishes_ping
    monkeypatch.setattr(app_module, "READINESS_DATABASE_TIMEOUT_SECONDS", 0.01)

    with TestClient(app) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == {"status": "unready", "missing": ["database"]}


def test_live_health_contract_schema_matches_the_versioned_response() -> None:
    contract_path = (
        Path(__file__).resolve().parents[3]
        / "packages"
        / "contracts"
        / "schemas"
        / "v1"
        / "health-live-response.schema.json"
    )
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    assert contract["required"] == ["status", "service", "api_version"]
    assert contract["additionalProperties"] is False
    assert contract["properties"]["status"]["const"] == "ok"
    assert contract["properties"]["api_version"]["const"] == "v1"
    assert contract["properties"]["service"]["pattern"] == "^[a-z][a-z0-9-]*$"


def test_openapi_health_response_schema_matches_the_canonical_contract() -> None:
    contract_path = (
        Path(__file__).resolve().parents[3]
        / "packages"
        / "contracts"
        / "schemas"
        / "v1"
        / "health-live-response.schema.json"
    )
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    openapi = create_app(Settings(service_name="api-test")).openapi()
    operation = openapi["paths"]["/api/v1/health/live"]["get"]
    response_schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
    component = openapi["components"]["schemas"]["HealthLiveResponse"]

    assert response_schema == {"$ref": "#/components/schemas/HealthLiveResponse"}
    assert component["required"] == contract["required"]
    assert component["additionalProperties"] is contract["additionalProperties"]
    for property_name, expected_constraints in contract["properties"].items():
        documented_property = component["properties"][property_name]
        for keyword, expected_value in expected_constraints.items():
            assert documented_property[keyword] == expected_value
