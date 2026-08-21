"""Tests for Deployment & Rollback subsystem (Phase 6)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from autonomous_sdo_api.app import create_app
from autonomous_sdo_api.config import Settings
from autonomous_sdo_api.database.tenancy import (
    OrganizationContext,
    get_organization_context,
)
from autonomous_sdo_api.deployment.models import (
    DeploymentApprovalPurpose,
    DeploymentEnvironment,
    DeploymentStatus,
    ExpandContractStep,
    MigrationRiskLevel,
    ReleaseStrategy,
)
from autonomous_sdo_api.deployment.service import DeploymentService
from autonomous_sdo_api.policy import Role

pytestmark = pytest.mark.unit


class TestDeploymentModels:
    def test_enums(self) -> None:
        assert ReleaseStrategy.CANARY.value == "canary"
        assert DeploymentEnvironment.PRODUCTION.value == "production"
        assert DeploymentStatus.ROLLED_BACK.value == "rolled_back"
        assert MigrationRiskLevel.HIGH.value == "high"
        assert ExpandContractStep.EXPAND.value == "expand"

    def test_approval_expiry_and_digest(self) -> None:
        from autonomous_sdo_api.deployment.models import DeploymentApprovalModel

        digest = "a" * 64
        approval = DeploymentApprovalModel(
            id="appr-1",
            plan_id="plan-1",
            approver_id="user-1",
            purpose=DeploymentApprovalPurpose.DEPLOY,
            artifact_digest=digest,
            environment=DeploymentEnvironment.STAGING,
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
        assert approval.is_expired() is True
        assert approval.is_digest_valid(digest) is True
        assert approval.is_digest_valid("b" * 64) is False


class TestDeploymentService:
    def test_create_and_list_release_plans(self) -> None:
        service = DeploymentService()
        org_id = uuid4()
        digest = "c" * 64

        plan = service.create_release_plan(
            organization_id=org_id,
            title="v1.0.0 Release",
            version="1.0.0",
            artifact_digest=digest,
            artifact_image="ghcr.io/org/repo:1.0.0",
            strategy="canary",
            target_environment="production",
            created_by="user-dev-1",
            migrations=[
                {
                    "migration_name": "add_audit_partition",
                    "version": "20260820_01",
                    "is_backward_compatible": True,
                    "expand_contract_step": "expand",
                    "estimated_duration_seconds": 20,
                    "risk_level": "low",
                }
            ],
            slo_gates=[
                {
                    "metric_name": "p99_latency_ms",
                    "target_value": 200.0,
                    "actual_value": 120.0,
                    "passed": True,
                    "unit": "ms",
                }
            ],
        )
        assert plan.status == DeploymentStatus.PENDING_APPROVAL
        assert len(plan.migrations) == 1
        assert len(plan.slo_gates) == 1

        plans = service.list_release_plans(org_id)
        assert len(plans) == 1
        assert plans[0].id == plan.id

    def test_tenant_isolation(self) -> None:
        service = DeploymentService()
        org1 = uuid4()
        org2 = uuid4()

        plan1 = service.create_release_plan(
            organization_id=org1,
            title="Org1 Release",
            version="1.0.0",
            artifact_digest="d" * 64,
            artifact_image="image:1",
            created_by="user-1",
        )

        assert service.get_release_plan(plan1.id, org1) is not None
        assert service.get_release_plan(plan1.id, org2) is None
        assert len(service.list_release_plans(org2)) == 0

    def test_separation_of_duties_enforced(self) -> None:
        service = DeploymentService()
        org_id = uuid4()
        digest = "e" * 64

        plan = service.create_release_plan(
            organization_id=org_id,
            title="Release 1",
            version="1.0.0",
            artifact_digest=digest,
            artifact_image="image:1",
            created_by="user-creator",
        )

        # Creator trying to approve must fail
        with pytest.raises(ValueError, match="Separation of duties"):
            service.submit_approval(
                plan_id=plan.id,
                organization_id=org_id,
                approver_id="user-creator",
                purpose="deploy",
                artifact_digest=digest,
            )

    def test_artifact_digest_mismatch_rejected(self) -> None:
        service = DeploymentService()
        org_id = uuid4()

        plan = service.create_release_plan(
            organization_id=org_id,
            title="Release 1",
            version="1.0.0",
            artifact_digest="f" * 64,
            artifact_image="image:1",
            created_by="user-creator",
        )

        with pytest.raises(ValueError, match="Artifact digest mismatch"):
            service.submit_approval(
                plan_id=plan.id,
                organization_id=org_id,
                approver_id="user-approver",
                purpose="deploy",
                artifact_digest="0" * 64,
            )

    def test_canary_rollout_and_slo_gate_promotion(self) -> None:
        service = DeploymentService()
        org_id = uuid4()
        digest = "1" * 64

        plan = service.create_release_plan(
            organization_id=org_id,
            title="Canary Release",
            version="1.1.0",
            artifact_digest=digest,
            artifact_image="image:canary",
            strategy="canary",
            created_by="user-creator",
            slo_gates=[
                {
                    "metric_name": "error_rate",
                    "target_value": 0.01,
                    "actual_value": 0.002,
                    "passed": True,
                    "unit": "%",
                }
            ],
        )

        # Approve and deploy
        service.submit_approval(
            plan_id=plan.id,
            organization_id=org_id,
            approver_id="user-rel-mgr",
            purpose="deploy",
            artifact_digest=digest,
        )
        service.start_deployment(plan.id, org_id)
        assert plan.status == DeploymentStatus.CANARY_VALIDATING

        # Promote canary
        promoted = service.promote_canary(plan.id, org_id)
        assert promoted is not None
        assert promoted.status == DeploymentStatus.COMPLETED
        assert promoted.completed_at is not None

    def test_separate_rollback_lifecycle(self) -> None:
        service = DeploymentService()
        org_id = uuid4()
        digest = "2" * 64

        plan = service.create_release_plan(
            organization_id=org_id,
            title="Rollback Candidate",
            version="1.2.0",
            artifact_digest=digest,
            artifact_image="image:candidate",
            created_by="user-creator",
        )

        # Deploy
        service.submit_approval(
            plan_id=plan.id,
            organization_id=org_id,
            approver_id="user-rel-mgr-1",
            purpose="deploy",
            artifact_digest=digest,
        )
        service.start_deployment(plan.id, org_id)

        # Request rollback
        service.request_rollback(
            plan_id=plan.id,
            organization_id=org_id,
            target_digest=digest,
            requested_by="user-oncall",
            reason="Performance degradation",
        )
        assert plan.status == DeploymentStatus.ROLLBACK_PENDING_APPROVAL

        # Executing without distinct rollback approval fails
        with pytest.raises(ValueError, match="distinct rollback approval"):
            service.execute_rollback(plan.id, org_id)

        # Submit purpose-separated rollback approval
        service.submit_approval(
            plan_id=plan.id,
            organization_id=org_id,
            approver_id="user-rel-mgr-2",
            purpose="rollback",
            artifact_digest=digest,
        )
        updated_plan = service.get_release_plan(plan.id, org_id)
        assert updated_plan is not None
        assert updated_plan.status == DeploymentStatus.ROLLBACK_APPROVED

        # Execute rollback and verify automated post-rollback checks
        rolled_back = service.execute_rollback(plan.id, org_id)
        assert rolled_back is not None
        assert rolled_back.status == DeploymentStatus.ROLLED_BACK
        assert len(rolled_back.post_rollback_checks) == 3
        assert all(c.passed for c in rolled_back.post_rollback_checks)


class TestDeploymentRoutes:
    def _make_client(self, org_id: UUID | None = None, user_id: str | None = None) -> TestClient:
        settings = Settings(
            service_name="test-deployment-api",
            database_url=None,
            oidc_issuer=None,
            oidc_audience=None,
            oidc_jwks=None,
        )
        app = create_app(settings)
        _org = org_id or uuid4()
        _user = user_id or str(uuid4())
        app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
            organization_id=_org,
            actor_id=_user,
            roles=frozenset({Role.RELEASE_MANAGER, Role.REPOSITORY_MAINTAINER}),
        )
        return TestClient(app)

    def test_full_deployment_api_flow(self) -> None:
        org_id = uuid4()
        client = self._make_client(org_id=org_id, user_id="user-creator")
        digest = "3" * 64

        # 1. Create plan
        resp = client.post(
            "/api/v1/deployment/plans",
            json={
                "title": "API Release",
                "version": "2.0.0",
                "artifact_digest": digest,
                "artifact_image": "ghcr.io/org/app:2.0.0",
                "strategy": "rolling",
                "target_environment": "production",
            },
        )
        assert resp.status_code == 201
        plan_id = resp.json()["id"]

        # 2. List plans
        resp = client.get("/api/v1/deployment/plans")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        # 3. Get plan by ID
        resp = client.get(f"/api/v1/deployment/plans/{plan_id}")
        assert resp.status_code == 200
        assert resp.json()["version"] == "2.0.0"

        # 4. Approve plan as distinct approver
        approver_client = self._make_client(org_id=org_id, user_id="user-approver")
        resp = approver_client.post(
            f"/api/v1/deployment/plans/{plan_id}/approvals",
            json={
                "purpose": "deploy",
                "artifact_digest": digest,
                "notes": "Approved for production",
            },
        )
        assert resp.status_code == 201

        # 5. Start deploy
        resp = approver_client.post(f"/api/v1/deployment/plans/{plan_id}/deploy")
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"

        # 6. Request rollback
        resp = approver_client.post(
            f"/api/v1/deployment/plans/{plan_id}/rollback-request",
            json={"target_digest": digest, "reason": "Issue detected"},
        )
        assert resp.status_code == 200

        # 7. Approve rollback as another distinct approver
        rollback_approver = self._make_client(org_id=org_id, user_id="user-approver-2")
        resp = rollback_approver.post(
            f"/api/v1/deployment/plans/{plan_id}/approvals",
            json={
                "purpose": "rollback",
                "artifact_digest": digest,
                "notes": "Rollback authorized",
            },
        )
        assert resp.status_code == 201

        # 8. Execute rollback
        resp = rollback_approver.post(f"/api/v1/deployment/plans/{plan_id}/rollback-execute")
        assert resp.status_code == 200
        assert resp.json()["status"] == "rolled_back"
        assert len(resp.json()["post_rollback_checks"]) == 3
