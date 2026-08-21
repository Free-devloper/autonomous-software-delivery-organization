from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from autonomous_sdo_api.database.tenancy import OrganizationContext, get_organization_context
from autonomous_sdo_api.policy import Action, AuthorizationPolicy
from autonomous_sdo_api.sandbox.controller import SandboxController
from autonomous_sdo_api.sandbox.models import (
    CreateSandboxRequest,
    ExecutionCommand,
    ExecutionResult,
    SandboxDescriptor,
    SandboxNotFoundError,
)

router = APIRouter(prefix="/api/v1/sandboxes", tags=["Sandboxes"])

_AUTH_POLICY = AuthorizationPolicy()
_SANDBOX_CONTROLLER = SandboxController()


def get_sandbox_controller() -> SandboxController:
    return _SANDBOX_CONTROLLER


@router.post(
    "",
    summary="Provision an isolated execution sandbox",
    status_code=status.HTTP_201_CREATED,
    response_model=SandboxDescriptor,
)
async def provision_sandbox(
    request: CreateSandboxRequest,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    controller: Annotated[SandboxController, Depends(get_sandbox_controller)],
) -> SandboxDescriptor:
    _AUTH_POLICY.require(context.roles, Action.READ_WORKFLOWS)
    return await controller.create_sandbox(context.organization_id, request)


@router.get(
    "",
    summary="List active sandboxes for tenant",
    response_model=list[SandboxDescriptor],
)
async def list_sandboxes(
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    controller: Annotated[SandboxController, Depends(get_sandbox_controller)],
) -> list[SandboxDescriptor]:
    _AUTH_POLICY.require(context.roles, Action.READ_WORKFLOWS)
    return controller.list_sandboxes(context.organization_id)


@router.get(
    "/{sandbox_id}",
    summary="Get sandbox details",
    response_model=SandboxDescriptor,
)
async def get_sandbox(
    sandbox_id: str,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    controller: Annotated[SandboxController, Depends(get_sandbox_controller)],
) -> SandboxDescriptor:
    _AUTH_POLICY.require(context.roles, Action.READ_WORKFLOWS)
    try:
        return controller.get_sandbox(context.organization_id, sandbox_id)
    except SandboxNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.post(
    "/{sandbox_id}/execute",
    summary="Execute a command inside the isolated sandbox",
    response_model=ExecutionResult,
)
async def execute_command(
    sandbox_id: str,
    command: ExecutionCommand,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    controller: Annotated[SandboxController, Depends(get_sandbox_controller)],
) -> ExecutionResult:
    _AUTH_POLICY.require(context.roles, Action.READ_WORKFLOWS)
    try:
        return await controller.execute_command(context.organization_id, sandbox_id, command)
    except SandboxNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.delete(
    "/{sandbox_id}",
    summary="Terminate sandbox and destroy isolated worktree",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def terminate_sandbox(
    sandbox_id: str,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    controller: Annotated[SandboxController, Depends(get_sandbox_controller)],
) -> None:
    _AUTH_POLICY.require(context.roles, Action.READ_WORKFLOWS)
    try:
        await controller.terminate_sandbox(context.organization_id, sandbox_id)
    except SandboxNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
