import os
import tempfile
from pathlib import Path
from uuid import UUID

from autonomous_sdo_api.sandbox.adapter import SandboxRuntimeAdapter
from autonomous_sdo_api.sandbox.firecracker import FirecrackerMicroVMAdapter
from autonomous_sdo_api.sandbox.models import (
    CreateSandboxRequest,
    ExecutionCommand,
    ExecutionResult,
    SandboxDescriptor,
    SandboxNotFoundError,
    SandboxProfile,
    SandboxStatus,
)
from autonomous_sdo_api.sandbox.rootless import RootlessContainerAdapter


class SandboxController:
    """Multi-tenant sandbox lifecycle manager and security coordinator."""

    def __init__(self, base_work_dir: Path | None = None) -> None:
        self.base_work_dir = base_work_dir or self._resolve_base_dir()
        self._sandboxes: dict[tuple[UUID, str], SandboxDescriptor] = {}
        self._adapters: dict[SandboxProfile, SandboxRuntimeAdapter] = {
            SandboxProfile.ROOTLESS_CONTAINER: RootlessContainerAdapter(
                self.base_work_dir / "rootless"
            ),
            SandboxProfile.FIRECRACKER_MICROVM: FirecrackerMicroVMAdapter(
                self.base_work_dir / "firecracker"
            ),
        }

    @staticmethod
    def _resolve_base_dir() -> Path:
        """Resolve sandbox working directory, tolerating read-only root filesystems."""
        env_dir = os.environ.get("ASDO_SANDBOX_DIR")
        if env_dir:
            return Path(env_dir)
        cwd_dir = Path(os.getcwd()) / ".sandboxes"
        try:
            cwd_dir.mkdir(parents=True, exist_ok=True)
            return cwd_dir
        except OSError:
            return Path(tempfile.gettempdir()) / "asdo-sandboxes"

    def _get_adapter(self, profile: SandboxProfile) -> SandboxRuntimeAdapter:
        return self._adapters.get(profile, self._adapters[SandboxProfile.ROOTLESS_CONTAINER])

    async def create_sandbox(
        self, organization_id: UUID, request: CreateSandboxRequest
    ) -> SandboxDescriptor:
        worktree_path = str(
            (self.base_work_dir / str(organization_id) / request.work_package_id).resolve()
        )
        descriptor = SandboxDescriptor(
            organization_id=organization_id,
            requirement_id=request.requirement_id,
            plan_id=request.plan_id,
            work_package_id=request.work_package_id,
            profile=request.profile,
            limits=request.limits,
            status=SandboxStatus.PROVISIONING,
            worktree_path=worktree_path,
        )

        adapter = self._get_adapter(request.profile)
        await adapter.provision(descriptor)

        key = (organization_id, descriptor.id)
        self._sandboxes[key] = descriptor
        return descriptor

    def get_sandbox(self, organization_id: UUID, sandbox_id: str) -> SandboxDescriptor:
        key = (organization_id, sandbox_id)
        if key not in self._sandboxes:
            raise SandboxNotFoundError(
                f"Sandbox '{sandbox_id}' not found for tenant '{organization_id}'"
            )
        return self._sandboxes[key]

    def list_sandboxes(self, organization_id: UUID) -> list[SandboxDescriptor]:
        return [desc for (org_id, _), desc in self._sandboxes.items() if org_id == organization_id]

    async def execute_command(
        self,
        organization_id: UUID,
        sandbox_id: str,
        command: ExecutionCommand,
    ) -> ExecutionResult:
        descriptor = self.get_sandbox(organization_id, sandbox_id)
        if descriptor.status == SandboxStatus.TERMINATED:
            descriptor.status = SandboxStatus.FAILED
            return ExecutionResult(
                sandbox_id=sandbox_id,
                exit_code=1,
                stdout="",
                stderr="Cannot execute commands in a terminated sandbox.",
                duration_ms=0.0,
            )

        descriptor.status = SandboxStatus.EXECUTING
        adapter = self._get_adapter(descriptor.profile)

        try:
            result = await adapter.execute(descriptor, command)
            descriptor.status = SandboxStatus.READY
            return result
        except Exception:
            descriptor.status = SandboxStatus.FAILED
            raise

    async def terminate_sandbox(self, organization_id: UUID, sandbox_id: str) -> None:
        descriptor = self.get_sandbox(organization_id, sandbox_id)
        adapter = self._get_adapter(descriptor.profile)
        await adapter.terminate(descriptor)
        key = (organization_id, sandbox_id)
        self._sandboxes.pop(key, None)
