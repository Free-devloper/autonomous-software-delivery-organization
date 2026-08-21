from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SandboxProfile(StrEnum):
    ROOTLESS_CONTAINER = "rootless_container"
    FIRECRACKER_MICROVM = "firecracker_microvm"


class NetworkPolicy(StrEnum):
    DENY_ALL = "deny_all"
    ALLOW_INTERNAL_ONLY = "allow_internal_only"


class SandboxStatus(StrEnum):
    PROVISIONING = "provisioning"
    READY = "ready"
    EXECUTING = "executing"
    TERMINATED = "terminated"
    FAILED = "failed"


class SandboxLimits(BaseModel):
    cpu_cores: float = Field(default=2.0, gt=0, le=16.0)
    memory_mb: int = Field(default=2048, gt=0, le=32768)
    disk_mb: int = Field(default=8192, gt=0, le=65536)
    timeout_seconds: int = Field(default=300, gt=0, le=3600)
    network_policy: NetworkPolicy = Field(default=NetworkPolicy.DENY_ALL)


class CreateSandboxRequest(BaseModel):
    requirement_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    work_package_id: str = Field(min_length=1)
    profile: SandboxProfile = Field(default=SandboxProfile.ROOTLESS_CONTAINER)
    limits: SandboxLimits = Field(default_factory=SandboxLimits)


class SandboxDescriptor(BaseModel):
    id: str = Field(default_factory=lambda: f"sbx_{uuid4().hex[:12]}")
    organization_id: UUID
    requirement_id: str
    plan_id: str
    work_package_id: str
    profile: SandboxProfile
    limits: SandboxLimits
    status: SandboxStatus = Field(default=SandboxStatus.PROVISIONING)
    worktree_path: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ExecutionCommand(BaseModel):
    command: str = Field(min_length=1)
    args: list[str] = Field(default_factory=list)
    working_dir: str | None = None
    environment: dict[str, str] = Field(default_factory=dict)
    ephemeral_secrets: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: int | None = Field(default=None, gt=0, le=3600)


class ExecutionResult(BaseModel):
    sandbox_id: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool = False
    redacted_secrets_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class SandboxNotFoundError(KeyError):
    pass


class SandboxSecurityViolation(Exception):
    pass


class PathTraversalViolation(SandboxSecurityViolation):
    pass


class SymlinkBreakoutViolation(SandboxSecurityViolation):
    pass


class ForbiddenMountViolation(SandboxSecurityViolation):
    pass


class NetworkEgressViolation(SandboxSecurityViolation):
    pass


class SandboxExecutionError(Exception):
    pass
