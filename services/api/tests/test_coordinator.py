"""Tests for Coordinator Agent and multi-agent specialist orchestration."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from autonomous_sdo_api.app import create_app
from autonomous_sdo_api.config import Settings
from autonomous_sdo_api.coordinator.models import (
    SpecialistRole,
    TaskHandoffStatus,
)
from autonomous_sdo_api.coordinator.service import CoordinatorAgentService
from autonomous_sdo_api.database.tenancy import (
    OrganizationContext,
    get_organization_context,
)
from autonomous_sdo_api.policy import Role

pytestmark = pytest.mark.unit


class TestCoordinatorService:
    def test_start_pipeline_orchestration(self) -> None:
        service = CoordinatorAgentService()
        org_id = uuid4()

        run = service.start_pipeline(
            organization_id=org_id,
            title="Implement User Registration",
            requirement_id="req-101",
        )
        assert run.status == TaskHandoffStatus.COMPLETED
        assert len(run.assignments) == 6
        assert len(run.artifact_digest) == 64

        # Verify all 6 specialist roles are represented in the pipeline
        roles = [a.role for a in run.assignments]
        assert SpecialistRole.ANALYST in roles
        assert SpecialistRole.ARCHITECT in roles
        assert SpecialistRole.CODER in roles
        assert SpecialistRole.TESTER in roles
        assert SpecialistRole.REVIEWER in roles
        assert SpecialistRole.RELEASE_MANAGER in roles

        runs = service.list_pipelines(org_id)
        assert len(runs) == 1
        assert runs[0].id == run.id

    def test_tenant_isolation(self) -> None:
        service = CoordinatorAgentService()
        org1 = uuid4()
        org2 = uuid4()

        run = service.start_pipeline(
            organization_id=org1,
            title="Org1 Task",
            requirement_id="req-1",
        )
        assert service.get_pipeline(run.id, org1) is not None
        assert service.get_pipeline(run.id, org2) is None
        assert len(service.list_pipelines(org2)) == 0


class TestCoordinatorRoutes:
    def _make_client(self, org_id: UUID | None = None) -> TestClient:
        settings = Settings(
            service_name="test-coordinator-api",
            database_url=None,
            oidc_issuer=None,
            oidc_audience=None,
            oidc_jwks=None,
        )
        app = create_app(settings)
        _org = org_id or uuid4()
        app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
            organization_id=_org,
            actor_id="user-coordinator",
            roles=frozenset({Role.ORGANIZATION_ADMINISTRATOR}),
        )
        return TestClient(app)

    def test_coordinator_api_flow(self) -> None:
        org_id = uuid4()
        client = self._make_client(org_id=org_id)

        # 1. Start pipeline
        resp = client.post(
            "/api/v1/coordinator/pipelines",
            json={"title": "Deliver Core Auth Feature", "requirement_id": "req-202"},
        )
        assert resp.status_code == 201
        run_id = resp.json()["id"]

        # 2. List pipelines
        resp = client.get("/api/v1/coordinator/pipelines")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        # 3. Get pipeline by ID
        resp = client.get(f"/api/v1/coordinator/pipelines/{run_id}")
        assert resp.status_code == 200
        assert len(resp.json()["assignments"]) == 6
