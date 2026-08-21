from __future__ import annotations

import asyncio
from datetime import UTC
from typing import cast
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from autonomous_sdo_api.app import create_app
from autonomous_sdo_api.config import Settings
from autonomous_sdo_api.database.identifiers import new_uuid7
from autonomous_sdo_api.database.models import OrganizationConfiguration, utc_now
from autonomous_sdo_api.database.repositories import OrganizationConfigurationRepository
from autonomous_sdo_api.database.services import OrganizationConfigurationService
from autonomous_sdo_api.database.session import (
    TenantScopedSessionFactory,
    create_tenant_session_factory,
)
from autonomous_sdo_api.database.tenancy import OrganizationContext, get_organization_context
from autonomous_sdo_api.policy import Role

pytestmark = pytest.mark.unit


class _Tx:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *_: object) -> None:
        return None


class _Session:
    def __init__(self) -> None:
        self.executions: list[tuple[str, dict[str, str]]] = []

    async def __aenter__(self) -> _Session:
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    def begin(self) -> _Tx:
        return _Tx()

    async def execute(self, statement: object, parameters: dict[str, str]) -> None:
        self.executions.append((str(statement), parameters))


class _Maker:
    def __init__(self, session: _Session) -> None:
        self.session = session

    def __call__(self) -> _Session:
        return self.session


class _StaticConfigurationRepository(OrganizationConfigurationRepository):
    def __init__(self, configuration: OrganizationConfiguration | None) -> None:
        self.configuration = configuration

    async def get_for_organization(
        self, session: AsyncSession, organization_id: UUID
    ) -> OrganizationConfiguration | None:
        return self.configuration


def test_new_uuid7_has_required_version_and_variant() -> None:
    identifier = new_uuid7()
    assert identifier.version == 7
    assert identifier.variant == "specified in RFC 4122"


def test_tenant_session_scope_sets_transaction_local_postgresql_context() -> None:
    organization_id = UUID("018f4b9d-4c5d-7abc-8def-0123456789ab")
    session = _Session()
    factory = TenantScopedSessionFactory(_Maker(session))  # type: ignore[arg-type]

    async def use_scope() -> None:
        async with factory.transaction(organization_id):
            pass

    asyncio.run(use_scope())
    assert session.executions == [
        (
            "SELECT set_config('asdo.organization_id', :organization_id, true)",
            {"organization_id": str(organization_id)},
        )
    ]


def test_repository_query_defense_in_depth_includes_organization_predicate() -> None:
    class RecordingSession:
        statement: object | None = None

        async def scalar(self, statement: object) -> None:
            self.statement = statement
            return None

    organization_id = UUID("018f4b9d-4c5d-7abc-8def-0123456789ab")
    session = RecordingSession()
    asyncio.run(
        OrganizationConfigurationRepository().get_for_organization(
            cast(AsyncSession, session), organization_id
        )
    )
    assert session.statement is not None
    compiled = str(session.statement)
    assert "organization_configurations.organization_id" in compiled
    assert ":organization_id_1" in compiled


def test_organization_configuration_endpoint_fails_closed_without_identity() -> None:
    with TestClient(create_app(Settings(service_name="api-test"))) as client:
        response = client.get("/api/v1/organization/configuration")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Organization identity is unavailable until authentication is configured."
    }


def test_organization_configuration_endpoint_returns_the_scoped_configuration() -> None:
    organization_id = UUID("018f4b9d-4c5d-7abc-8def-0123456789ab")
    now = utc_now()
    configuration = OrganizationConfiguration(
        id=new_uuid7(),
        organization_id=organization_id,
        data_region="eu-central-1",
        data_classification="confidential",
        created_at=now,
        updated_at=now,
    )
    session = _Session()
    service = OrganizationConfigurationService(
        TenantScopedSessionFactory(_Maker(session)),  # type: ignore[arg-type]
        _StaticConfigurationRepository(configuration),
    )
    app = create_app(Settings(service_name="api-test"))
    app.state.organization_configuration_service = service
    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        organization_id,
        actor_id="viewer",
        roles=frozenset({Role.READ_ONLY_VIEWER}),
    )

    with TestClient(app) as client:
        response = client.get("/api/v1/organization/configuration")

    assert response.status_code == 200
    assert response.json() == {
        "organization_id": str(organization_id),
        "data_region": "eu-central-1",
        "data_classification": "confidential",
    }
    assert session.executions[0][1] == {"organization_id": str(organization_id)}


def test_organization_configuration_endpoint_reports_not_found_for_scoped_absence() -> None:
    organization_id = UUID("018f4b9d-4c5d-7abc-8def-0123456789ab")
    session = _Session()
    service = OrganizationConfigurationService(
        TenantScopedSessionFactory(_Maker(session)),  # type: ignore[arg-type]
        _StaticConfigurationRepository(None),
    )
    app = create_app(Settings(service_name="api-test"))
    app.state.organization_configuration_service = service
    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        organization_id,
        actor_id="viewer",
        roles=frozenset({Role.READ_ONLY_VIEWER}),
    )

    with TestClient(app) as client:
        response = client.get("/api/v1/organization/configuration")

    assert response.status_code == 404


def test_organization_configuration_endpoint_reports_unavailable_persistence_after_identity() -> (
    None
):
    app = create_app(Settings(service_name="api-test"))
    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        new_uuid7(),
        actor_id="viewer",
        roles=frozenset({Role.READ_ONLY_VIEWER}),
    )

    with TestClient(app) as client:
        response = client.get("/api/v1/organization/configuration")

    assert response.status_code == 503
    assert response.json() == {"detail": "Organization persistence is unavailable."}


def test_organization_configuration_endpoint_rejects_authenticated_actor_without_role() -> None:
    organization_id = UUID("018f4b9d-4c5d-7abc-8def-0123456789ab")
    now = utc_now()
    configuration = OrganizationConfiguration(
        id=new_uuid7(),
        organization_id=organization_id,
        data_region="eu-central-1",
        data_classification="confidential",
        created_at=now,
        updated_at=now,
    )
    session = _Session()
    service = OrganizationConfigurationService(
        TenantScopedSessionFactory(_Maker(session)),  # type: ignore[arg-type]
        _StaticConfigurationRepository(configuration),
    )
    app = create_app(Settings(service_name="api-test"))
    app.state.organization_configuration_service = service
    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        organization_id,
        actor_id="requester",
        roles=frozenset({Role.REQUESTER}),
    )

    with TestClient(app) as client:
        response = client.get("/api/v1/organization/configuration")

    assert response.status_code == 403
    assert response.json() == {
        "detail": "The authenticated actor is not authorized for this action."
    }


def test_timestamp_and_async_session_factory_use_utc_and_asyncpg() -> None:
    assert utc_now().tzinfo is UTC
    factory = create_tenant_session_factory("postgresql+asyncpg://app:password@localhost:5432/asdo")
    assert isinstance(factory, TenantScopedSessionFactory)
    asyncio.run(factory.close())


def test_tenant_session_factory_disposes_its_owned_engine() -> None:
    engine = create_async_engine("postgresql+asyncpg://app:password@localhost:5432/asdo")
    dispose = AsyncMock()

    with patch.object(AsyncEngine, "dispose", dispose):
        asyncio.run(TenantScopedSessionFactory(engine).close())

    dispose.assert_awaited_once_with()


def test_application_lifespan_closes_its_owned_tenant_session_factory() -> None:
    settings = Settings.model_validate(
        {
            "service_name": "api-test",
            "database_url": "postgresql+asyncpg://app:password@localhost:5432/asdo",
        }
    )
    app = create_app(settings)
    factory = cast(TenantScopedSessionFactory, app.state.tenant_session_factory)
    close = AsyncMock()

    with patch.object(factory, "close", close), TestClient(app):
        pass

    close.assert_awaited_once_with()
