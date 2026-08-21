"""FastAPI routes for security scanning and quality gates."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from autonomous_sdo_api.database.tenancy import (
    OrganizationContext,
    get_organization_context,
)
from autonomous_sdo_api.security.gates import QualityGateEngine
from autonomous_sdo_api.security.models import (
    MutationReport,
    QualityGateEvaluation,
    SecurityScanReport,
    TestSuiteReport,
)
from autonomous_sdo_api.security.scanner import SecurityScanner

security_router = APIRouter(prefix="/api/v1/security", tags=["security"])

# In-memory storage keyed by (organization_id, report_id)
_SCAN_REPORTS: dict[tuple[UUID, str], SecurityScanReport] = {}
_TEST_REPORTS: dict[tuple[UUID, str], TestSuiteReport] = {}
_MUTATION_REPORTS: dict[tuple[UUID, str], MutationReport] = {}
_GATE_EVALS: dict[tuple[UUID, str], QualityGateEvaluation] = {}

_SCANNER = SecurityScanner()
_GATE_ENGINE = QualityGateEngine()


class _ScanRequest:
    """Body for scan endpoint (avoid Pydantic for simplicity)."""


@security_router.post(
    "/scans",
    response_model=SecurityScanReport,
    status_code=status.HTTP_201_CREATED,
    summary="Run a security scan against source files",
)
async def create_scan(
    request: dict[str, Any],
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> SecurityScanReport:
    scan_target = request.get("scan_target", "unknown")
    source_files: dict[str, str] = request.get("source_files", {})
    if not source_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="source_files is required.",
        )

    report = SecurityScanner.scan_source_files(
        organization_id=context.organization_id,
        scan_target=str(scan_target),
        source_files=source_files,
    )
    _SCAN_REPORTS[(context.organization_id, report.id)] = report
    return report


@security_router.get(
    "/scans",
    response_model=list[SecurityScanReport],
    summary="List security scan reports for current tenant",
)
async def list_scans(
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> list[SecurityScanReport]:
    return [r for (org_id, _), r in _SCAN_REPORTS.items() if org_id == context.organization_id]


@security_router.get(
    "/scans/{scan_id}",
    response_model=SecurityScanReport,
    summary="Get a security scan report by ID",
)
async def get_scan(
    scan_id: str,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> SecurityScanReport:
    report = _SCAN_REPORTS.get((context.organization_id, scan_id))
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan report not found.",
        )
    return report


@security_router.post(
    "/test-reports",
    response_model=TestSuiteReport,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a test suite report",
)
async def create_test_report(
    report: TestSuiteReport,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> TestSuiteReport:
    _TEST_REPORTS[(context.organization_id, report.id)] = report
    return report


@security_router.get(
    "/test-reports",
    response_model=list[TestSuiteReport],
    summary="List test suite reports for current tenant",
)
async def list_test_reports(
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> list[TestSuiteReport]:
    return [r for (org_id, _), r in _TEST_REPORTS.items() if org_id == context.organization_id]


@security_router.post(
    "/mutation-reports",
    response_model=MutationReport,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a mutation testing report",
)
async def create_mutation_report(
    report: MutationReport,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> MutationReport:
    _MUTATION_REPORTS[(context.organization_id, report.id)] = report
    return report


@security_router.post(
    "/quality-gates/evaluate",
    response_model=QualityGateEvaluation,
    status_code=status.HTTP_200_OK,
    summary="Evaluate quality gates for a work package",
)
async def evaluate_quality_gates(
    request: dict[str, Any],
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> QualityGateEvaluation:
    wp_id = request.get("work_package_id")
    if not wp_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="work_package_id is required.",
        )

    test_report_id = request.get("test_report_id")
    mutation_report_id = request.get("mutation_report_id")
    scan_report_ids: list[str] = request.get("scan_report_ids", [])

    test_report = None
    if test_report_id:
        test_report = _TEST_REPORTS.get((context.organization_id, test_report_id))

    mutation_report = None
    if mutation_report_id:
        mutation_report = _MUTATION_REPORTS.get((context.organization_id, mutation_report_id))

    scan_reports = [
        _SCAN_REPORTS[(context.organization_id, sid)]
        for sid in scan_report_ids
        if (context.organization_id, sid) in _SCAN_REPORTS
    ]

    evaluation = _GATE_ENGINE.evaluate(
        organization_id=context.organization_id,
        work_package_id=str(wp_id),
        test_report=test_report,
        mutation_report=mutation_report,
        scan_reports=scan_reports or None,
    )
    _GATE_EVALS[(context.organization_id, evaluation.id)] = evaluation
    return evaluation
