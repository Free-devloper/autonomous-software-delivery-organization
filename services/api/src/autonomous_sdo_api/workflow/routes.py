from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from autonomous_sdo_api.database.tenancy import OrganizationContext, get_organization_context
from autonomous_sdo_api.policy import Action, AuthorizationPolicy
from autonomous_sdo_api.workflow.engine import WorkflowExecutionEngine
from autonomous_sdo_api.workflow.models import (
    CheckpointNotFoundError,
    InvalidWorkflowStateTransitionError,
    RollbackWorkflowRequest,
    SignalWorkflowRequest,
    StartWorkflowRequest,
    WorkflowCheckpoint,
    WorkflowExecution,
    WorkflowNotFoundError,
)

router = APIRouter(prefix="/api/v1/workflows", tags=["Workflows"])

_AUTH_POLICY = AuthorizationPolicy()
_ENGINE = WorkflowExecutionEngine()


def get_workflow_engine() -> WorkflowExecutionEngine:
    return _ENGINE


@router.post(
    "",
    response_model=WorkflowExecution,
    status_code=status.HTTP_201_CREATED,
    summary="Start a durable workflow run",
)
async def start_workflow(
    payload: StartWorkflowRequest,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    engine: Annotated[WorkflowExecutionEngine, Depends(get_workflow_engine)],
) -> WorkflowExecution:
    _AUTH_POLICY.require(context.roles, Action.MANAGE_WORKFLOWS)
    return engine.start_workflow(
        org_id=context.organization_id,
        requirement_id=payload.requirement_id,
        plan_id=payload.plan_id,
        initial_payload=payload.initial_payload,
        actor_id=context.actor_id,
    )


@router.get(
    "/{workflow_id}",
    response_model=WorkflowExecution,
    summary="Get workflow execution instance",
)
async def get_workflow(
    workflow_id: str,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    engine: Annotated[WorkflowExecutionEngine, Depends(get_workflow_engine)],
) -> WorkflowExecution:
    _AUTH_POLICY.require(context.roles, Action.READ_WORKFLOWS)
    try:
        return engine.get_workflow(context.organization_id, workflow_id)
    except WorkflowNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.post(
    "/{workflow_id}/signal",
    response_model=WorkflowExecution,
    summary="Deliver a signal to advance or alter workflow execution",
)
async def signal_workflow(
    workflow_id: str,
    payload: SignalWorkflowRequest,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    engine: Annotated[WorkflowExecutionEngine, Depends(get_workflow_engine)],
) -> WorkflowExecution:
    _AUTH_POLICY.require(context.roles, Action.MANAGE_WORKFLOWS)
    try:
        return engine.send_signal(
            org_id=context.organization_id,
            workflow_id=workflow_id,
            signal_name=payload.signal_name,
            payload=payload.payload,
            actor_id=context.actor_id,
        )
    except WorkflowNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    except InvalidWorkflowStateTransitionError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err


@router.get(
    "/{workflow_id}/checkpoints",
    response_model=list[WorkflowCheckpoint],
    summary="List all checkpoints for a workflow execution",
)
async def list_checkpoints(
    workflow_id: str,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    engine: Annotated[WorkflowExecutionEngine, Depends(get_workflow_engine)],
) -> list[WorkflowCheckpoint]:
    _AUTH_POLICY.require(context.roles, Action.READ_WORKFLOWS)
    try:
        return engine.list_checkpoints(context.organization_id, workflow_id)
    except WorkflowNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.post(
    "/{workflow_id}/rollback",
    response_model=WorkflowExecution,
    summary="Rollback workflow to a previous checkpoint",
)
async def rollback_workflow(
    workflow_id: str,
    payload: RollbackWorkflowRequest,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    engine: Annotated[WorkflowExecutionEngine, Depends(get_workflow_engine)],
) -> WorkflowExecution:
    _AUTH_POLICY.require(context.roles, Action.MANAGE_WORKFLOWS)
    try:
        return engine.rollback_to_checkpoint(
            org_id=context.organization_id,
            workflow_id=workflow_id,
            checkpoint_id=payload.checkpoint_id,
        )
    except (WorkflowNotFoundError, CheckpointNotFoundError) as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
