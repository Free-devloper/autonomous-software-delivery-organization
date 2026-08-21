"""Tests for Evaluation, Cost Analytics, and Disaster Recovery (Phase 7)."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from autonomous_sdo_api.app import create_app
from autonomous_sdo_api.config import Settings
from autonomous_sdo_api.database.tenancy import (
    OrganizationContext,
    get_organization_context,
)
from autonomous_sdo_api.evaluation.models import (
    BackupStatus,
    BackupType,
    EvaluationCategory,
    EvaluationStatus,
)
from autonomous_sdo_api.evaluation.service import EvaluationService
from autonomous_sdo_api.policy import Role

pytestmark = pytest.mark.unit


class TestEvaluationModels:
    def test_enums(self) -> None:
        assert EvaluationCategory.CORRECTNESS.value == "correctness"
        assert EvaluationCategory.SECURITY_RECALL.value == "security_recall"
        assert EvaluationStatus.PASSED.value == "passed"
        assert BackupType.FULL.value == "full"
        assert BackupStatus.COMPLETED.value == "completed"


class TestEvaluationService:
    def test_run_full_evaluation(self) -> None:
        service = EvaluationService()
        org_id = uuid4()

        report = service.run_evaluation(
            organization_id=org_id,
            run_id="run-001",
        )
        assert report.overall_status == EvaluationStatus.PASSED
        assert len(report.metrics) == 7
        assert all(m.passed for m in report.metrics)

        reports = service.list_evaluation_reports(org_id)
        assert len(reports) == 1
        assert reports[0].id == report.id

    def test_custom_metric_evaluation_failure(self) -> None:
        service = EvaluationService()
        org_id = uuid4()

        report = service.run_evaluation(
            organization_id=org_id,
            run_id="run-custom",
            custom_metrics=[
                {
                    "name": "coverage",
                    "category": "correctness",
                    "score": 75.0,
                    "target_threshold": 90.0,
                    "passed": False,
                    "unit": "%",
                    "details": "Under threshold",
                }
            ],
        )
        assert report.overall_status == EvaluationStatus.FAILED

    def test_cost_report_generation(self) -> None:
        service = EvaluationService()
        org_id = uuid4()

        cost = service.generate_cost_report(
            organization_id=org_id,
            budget_limit_usd=100.0,
            model_usages=[
                {
                    "model_name": "claude-3-5-sonnet",
                    "input_tokens": 100000,
                    "output_tokens": 20000,
                    "total_tokens": 120000,
                    "estimated_cost_usd": 15.50,
                }
            ],
        )
        assert cost.total_cost_usd == 15.50
        assert cost.is_within_budget is True
        assert cost.budget_consumed_percentage == 15.50

    def test_backup_and_restore_cycle(self) -> None:
        service = EvaluationService()
        org_id = uuid4()

        backup = service.create_backup_job(
            organization_id=org_id,
            backup_type="database",
            storage_uri="s3://backups/db.tar.gz",
            size_bytes=102400,
        )
        assert backup.status == BackupStatus.COMPLETED
        assert len(backup.artifact_digest) == 64
        assert len(service.list_backups(org_id)) == 1

        restore = service.create_restore_job(
            organization_id=org_id,
            backup_id=backup.id,
        )
        assert restore.status == BackupStatus.COMPLETED
        assert restore.data_integrity_verified is True
        assert restore.observed_recovery_time_seconds == 180

    def test_tenant_isolation(self) -> None:
        service = EvaluationService()
        org1 = uuid4()
        org2 = uuid4()

        rep = service.run_evaluation(organization_id=org1, run_id="run-1")
        assert service.get_evaluation_report(rep.id, org1) is not None
        assert service.get_evaluation_report(rep.id, org2) is None
        assert len(service.list_evaluation_reports(org2)) == 0


class TestEvaluationRoutes:
    def _make_client(self, org_id: UUID | None = None) -> TestClient:
        settings = Settings(
            service_name="test-evaluation-api",
            database_url=None,
            oidc_issuer=None,
            oidc_audience=None,
            oidc_jwks=None,
        )
        app = create_app(settings)
        _org = org_id or uuid4()
        app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
            organization_id=_org,
            actor_id="user-evaluator",
            roles=frozenset({Role.ORGANIZATION_ADMINISTRATOR, Role.AUDITOR}),
        )
        return TestClient(app)

    def test_evaluation_api_flow(self) -> None:
        org_id = uuid4()
        client = self._make_client(org_id=org_id)

        # 1. Run evaluation
        resp = client.post("/api/v1/evaluation/reports", json={"run_id": "eval-run-1"})
        assert resp.status_code == 201
        report_id = resp.json()["id"]

        # 2. List reports
        resp = client.get("/api/v1/evaluation/reports")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        # 3. Get report by ID
        resp = client.get(f"/api/v1/evaluation/reports/{report_id}")
        assert resp.status_code == 200
        assert resp.json()["overall_status"] == "passed"

        # 4. Generate cost report
        resp = client.post(
            "/api/v1/evaluation/cost-report",
            json={"budget_limit_usd": 250.0},
        )
        assert resp.status_code == 200
        assert resp.json()["is_within_budget"] is True

        # 5. Create backup
        resp = client.post("/api/v1/evaluation/backups", json={"backup_type": "full"})
        assert resp.status_code == 201
        backup_id = resp.json()["id"]

        # 6. List backups
        resp = client.get("/api/v1/evaluation/backups")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        # 7. Create restore drill
        resp = client.post("/api/v1/evaluation/restores", json={"backup_id": backup_id})
        assert resp.status_code == 201
        assert resp.json()["data_integrity_verified"] is True
