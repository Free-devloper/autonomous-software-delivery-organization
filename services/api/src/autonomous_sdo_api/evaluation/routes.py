"""FastAPI routes for evaluation, cost analytics, and disaster recovery."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from autonomous_sdo_api.database.tenancy import (
    OrganizationContext,
    get_organization_context,
)
from autonomous_sdo_api.evaluation.models import (
    BackupJobModel,
    CostReportModel,
    EvaluationReportModel,
    RestoreJobModel,
)
from autonomous_sdo_api.evaluation.service import EvaluationService

evaluation_router = APIRouter(prefix="/api/v1/evaluation", tags=["evaluation"])

_evaluation_service = EvaluationService()


@evaluation_router.post(
    "/reports",
    response_model=EvaluationReportModel,
    status_code=status.HTTP_201_CREATED,
    summary="Run full evaluation across production readiness thresholds",
)
async def run_evaluation(
    request: dict[str, Any],
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> EvaluationReportModel:
    report = _evaluation_service.run_evaluation(
        organization_id=context.organization_id,
        run_id=request.get("run_id", "run-default"),
        custom_metrics=request.get("custom_metrics"),
    )
    return report


@evaluation_router.get(
    "/reports",
    response_model=list[EvaluationReportModel],
    summary="List evaluation reports for current organization",
)
async def list_evaluation_reports(
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> list[EvaluationReportModel]:
    return _evaluation_service.list_evaluation_reports(context.organization_id)


@evaluation_router.get(
    "/reports/{report_id}",
    response_model=EvaluationReportModel,
    summary="Get an evaluation report by ID",
)
async def get_evaluation_report(
    report_id: str,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> EvaluationReportModel:
    report = _evaluation_service.get_evaluation_report(report_id, context.organization_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation report not found",
        )
    return report


@evaluation_router.post(
    "/cost-report",
    response_model=CostReportModel,
    summary="Generate cost and budget analytics report",
)
async def generate_cost_report(
    request: dict[str, Any],
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> CostReportModel:
    return _evaluation_service.generate_cost_report(
        organization_id=context.organization_id,
        budget_limit_usd=float(request.get("budget_limit_usd", 500.0)),
        model_usages=request.get("model_usages"),
    )


@evaluation_router.post(
    "/backups",
    response_model=BackupJobModel,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger an immutable backup snapshot",
)
async def create_backup(
    request: dict[str, Any],
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> BackupJobModel:
    return _evaluation_service.create_backup_job(
        organization_id=context.organization_id,
        backup_type=request.get("backup_type", "full"),
        storage_uri=request.get("storage_uri", "s3://backups/asdo/snapshot.tar.gz"),
        size_bytes=int(request.get("size_bytes", 52428800)),
    )


@evaluation_router.get(
    "/backups",
    response_model=list[BackupJobModel],
    summary="List all backup snapshots",
)
async def list_backups(
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> list[BackupJobModel]:
    return _evaluation_service.list_backups(context.organization_id)


@evaluation_router.post(
    "/restores",
    response_model=RestoreJobModel,
    status_code=status.HTTP_201_CREATED,
    summary="Run an automated disaster recovery restore drill",
)
async def create_restore(
    request: dict[str, Any],
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
) -> RestoreJobModel:
    try:
        return _evaluation_service.create_restore_job(
            organization_id=context.organization_id,
            backup_id=request.get("backup_id", ""),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
