"""Tests for Phase 4: Security scanner, quality gates, and API routes."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from autonomous_sdo_api.app import create_app
from autonomous_sdo_api.config import Settings
from autonomous_sdo_api.security.gates import QualityGateEngine
from autonomous_sdo_api.security.models import (
    CoverageEntry,
    FindingSeverity,
    MutationReport,
    QualityGateStatus,
    ScanToolCategory,
    SecurityFinding,
    TestSuiteReport,
    compute_scan_digest,
)
from autonomous_sdo_api.security.scanner import SecurityScanner

pytestmark = pytest.mark.unit


def test_security_finding_model() -> None:
    finding = SecurityFinding(
        id="f-001",
        rule_id="B101",
        tool="asdo-sast",
        category=ScanToolCategory.SAST,
        severity=FindingSeverity.HIGH,
        message="Use of eval detected",
        file_path="src/main.py",
        start_line=10,
    )
    assert finding.severity == FindingSeverity.HIGH
    assert finding.suppressed is False


def test_compute_scan_digest_deterministic() -> None:
    findings = [
        SecurityFinding(
            id="f1",
            rule_id="B101",
            tool="t",
            category=ScanToolCategory.SAST,
            severity=FindingSeverity.HIGH,
            message="msg",
            file_path="b.py",
            start_line=2,
        ),
        SecurityFinding(
            id="f2",
            rule_id="B102",
            tool="t",
            category=ScanToolCategory.SAST,
            severity=FindingSeverity.MEDIUM,
            message="msg2",
            file_path="a.py",
            start_line=1,
        ),
    ]
    d1 = compute_scan_digest("tool", "target", findings)
    d2 = compute_scan_digest("tool", "target", list(reversed(findings)))
    assert len(d1) == 64
    assert d1 == d2


def test_scanner_detects_eval() -> None:
    org_id = uuid4()
    source = {
        "main.py": 'result = eval("1 + 2")\n',
    }
    report = SecurityScanner.scan_source_files(
        organization_id=org_id,
        scan_target="test",
        source_files=source,
    )
    assert report.total_findings >= 1
    eval_findings = [f for f in report.findings if f.rule_id == "B307"]
    assert len(eval_findings) == 1


def test_scanner_detects_secrets() -> None:
    org_id = uuid4()
    source = {
        "config.py": "password = 'supersecretpassword123'\n",
    }
    report = SecurityScanner.scan_source_files(
        organization_id=org_id,
        scan_target="test",
        source_files=source,
    )
    secret_findings = [f for f in report.findings if f.rule_id == "B105"]
    assert len(secret_findings) >= 1
    assert report.passed is False  # high finding


def test_scanner_clean_code_passes() -> None:
    org_id = uuid4()
    source = {
        "clean.py": "def add(a: int, b: int) -> int:\n    return a + b\n",
    }
    report = SecurityScanner.scan_source_files(
        organization_id=org_id,
        scan_target="test",
        source_files=source,
    )
    assert report.total_findings == 0
    assert report.passed is True


def test_quality_gate_all_pass() -> None:
    engine = QualityGateEngine(
        coverage_threshold=90.0,
        mutation_threshold=80.0,
    )
    test_report = TestSuiteReport(
        id="tr-1",
        organization_id=uuid4(),
        suite_name="unit",
        total_tests=50,
        passed=50,
        failed=0,
        skipped=0,
        flaky=0,
        duration_ms=5000,
        coverage=[
            CoverageEntry(
                file_path="src/main.py",
                statement_coverage=95,
                branch_coverage=92,
                function_coverage=100,
                line_coverage=94,
            )
        ],
        overall_passed=True,
    )
    mutation = MutationReport(
        id="mr-1",
        organization_id=uuid4(),
        total_mutants=100,
        killed=85,
        survived=10,
        timeout=3,
        no_coverage=2,
        mutation_score=85.0,
        threshold=80.0,
        passed=True,
    )
    evaluation = engine.evaluate(
        organization_id=uuid4(),
        work_package_id="wp-1",
        test_report=test_report,
        mutation_report=mutation,
    )
    assert evaluation.overall_status == QualityGateStatus.PASSED


def test_quality_gate_fails_on_test_failures() -> None:
    engine = QualityGateEngine()
    test_report = TestSuiteReport(
        id="tr-2",
        organization_id=uuid4(),
        suite_name="unit",
        total_tests=50,
        passed=45,
        failed=5,
        skipped=0,
        flaky=0,
        duration_ms=5000,
        overall_passed=False,
    )
    evaluation = engine.evaluate(
        organization_id=uuid4(),
        work_package_id="wp-2",
        test_report=test_report,
    )
    assert evaluation.overall_status == QualityGateStatus.FAILED
    fail_checks = [c for c in evaluation.checks if c.name == "test_pass_rate"]
    assert len(fail_checks) == 1
    assert fail_checks[0].status == QualityGateStatus.FAILED


def test_quality_gate_warns_on_flaky() -> None:
    engine = QualityGateEngine(max_flaky_tests=2)
    test_report = TestSuiteReport(
        id="tr-3",
        organization_id=uuid4(),
        suite_name="unit",
        total_tests=50,
        passed=50,
        failed=0,
        skipped=0,
        flaky=5,
        duration_ms=5000,
        overall_passed=True,
    )
    evaluation = engine.evaluate(
        organization_id=uuid4(),
        work_package_id="wp-3",
        test_report=test_report,
    )
    assert evaluation.overall_status == QualityGateStatus.WARNING
    flaky_checks = [c for c in evaluation.checks if c.name == "flaky_test_limit"]
    assert len(flaky_checks) == 1
    assert flaky_checks[0].status == QualityGateStatus.WARNING


def test_security_api_routes() -> None:
    settings = Settings(service_name="asdo-security-api-test")
    app = create_app(settings=settings)
    client = TestClient(app)

    org_id = uuid4()

    from autonomous_sdo_api.database.tenancy import (
        OrganizationContext,
        get_organization_context,
    )
    from autonomous_sdo_api.policy import Role

    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        organization_id=org_id,
        actor_id="user-security-1",
        roles=frozenset({Role.SECURITY_REVIEWER}),
    )

    # 1. Create a scan
    res = client.post(
        "/api/v1/security/scans",
        json={
            "scan_target": "services/api",
            "source_files": {
                "main.py": 'result = eval("code")\n',
            },
        },
    )
    assert res.status_code == 201
    data = res.json()
    scan_id = data["id"]
    assert data["total_findings"] >= 1
    assert data["passed"] is True  # eval is medium, not high

    # 2. List scans
    res_list = client.get("/api/v1/security/scans")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # 3. Get scan by ID
    res_get = client.get(f"/api/v1/security/scans/{scan_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == scan_id

    # 4. Cross-tenant isolation
    other_org = uuid4()
    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        organization_id=other_org,
        actor_id="user-other",
        roles=frozenset({Role.SECURITY_REVIEWER}),
    )
    res_other = client.get("/api/v1/security/scans")
    assert res_other.status_code == 200
    assert len(res_other.json()) == 0

    # 5. Submit test report and evaluate quality gate
    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        organization_id=org_id,
        actor_id="user-security-1",
        roles=frozenset({Role.SECURITY_REVIEWER}),
    )
    test_report = {
        "id": "tr-api-1",
        "organization_id": str(org_id),
        "suite_name": "unit",
        "total_tests": 100,
        "passed": 100,
        "failed": 0,
        "skipped": 0,
        "flaky": 0,
        "duration_ms": 5000,
        "overall_passed": True,
        "run_at": "2026-08-20T10:00:00Z",
    }
    res_tr = client.post("/api/v1/security/test-reports", json=test_report)
    assert res_tr.status_code == 201

    res_gate = client.post(
        "/api/v1/security/quality-gates/evaluate",
        json={
            "work_package_id": "wp-api-1",
            "test_report_id": "tr-api-1",
            "scan_report_ids": [scan_id],
        },
    )
    assert res_gate.status_code == 200
    gate_data = res_gate.json()
    assert gate_data["work_package_id"] == "wp-api-1"
    assert len(gate_data["checks"]) >= 1
