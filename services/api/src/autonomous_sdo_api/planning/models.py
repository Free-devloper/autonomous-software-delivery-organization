from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class SpecialistRole(StrEnum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    TESTING = "testing"
    REVIEWER = "reviewer"


class WorkPackageBudget(BaseModel):
    """Budget constraints allocated to a work package or plan."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    max_tokens: int = Field(default=100000, gt=0)
    max_duration_seconds: int = Field(default=600, gt=0)
    max_cost_usd: float = Field(default=5.0, ge=0.0)


class WorkPackageStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkPackage(BaseModel):
    """An atomic, bounded unit of engineering work."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    requirement_id: str = Field(min_length=1)
    revision_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    target_files: list[str] = Field(min_length=1)
    acceptance_criteria_ids: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    assigned_specialist: SpecialistRole
    budget: WorkPackageBudget
    status: WorkPackageStatus = WorkPackageStatus.PENDING
    created_at: datetime


class DagEdge(BaseModel):
    """Dependency edge between two work packages."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    from_package_id: str = Field(min_length=1)
    to_package_id: str = Field(min_length=1)


class ArchitecturePlan(BaseModel):
    """Decomposition of a requirement revision into a dependency DAG of work packages."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    requirement_id: str = Field(min_length=1)
    revision_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    work_packages: list[WorkPackage] = Field(min_length=1)
    edges: list[DagEdge] = Field(default_factory=list)
    total_budget: WorkPackageBudget
    is_approved: bool = False
    approval_rationale: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    created_at: datetime


class CreatePlanRequest(BaseModel):
    """Payload to create an architecture plan."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    requirement_id: str = Field(min_length=1)
    revision_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    work_packages: list[WorkPackage] = Field(min_length=1)
    edges: list[DagEdge] = Field(default_factory=list)


class ApprovePlanRequest(BaseModel):
    """Payload to approve an architecture plan."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rationale: str = Field(min_length=1)


class PlanningError(Exception):
    """Base planning domain exception."""


class PlanNotFoundError(PlanningError):
    """Architecture plan not found."""


class CyclicDependencyError(PlanningError):
    """Execution DAG contains a circular dependency."""


class BudgetExceededError(PlanningError):
    """Plan exceeds allowable resource budget."""
