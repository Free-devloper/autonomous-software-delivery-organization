"""Data models for Coordinator Agent and multi-agent specialist orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class SpecialistRole(StrEnum):
    COORDINATOR = "coordinator"
    ANALYST = "analyst"
    ARCHITECT = "architect"
    CODER = "coder"
    TESTER = "tester"
    REVIEWER = "reviewer"
    RELEASE_MANAGER = "release_manager"


class TaskHandoffStatus(StrEnum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    REJECTED = "rejected"


class SpecialistAssignment(BaseModel):
    """Specific bounded task assigned by the coordinator to a specialist agent."""

    id: str
    role: SpecialistRole
    task_name: str
    owned_files: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    status: TaskHandoffStatus = TaskHandoffStatus.QUEUED
    output_summary: str = ""
    assigned_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None


class MultiAgentPipelineRun(BaseModel):
    """Complete multi-agent execution pipeline orchestrated by CoordinatorAgent."""

    id: str
    organization_id: UUID
    title: str
    requirement_id: str
    status: TaskHandoffStatus = TaskHandoffStatus.QUEUED
    assignments: list[SpecialistAssignment] = Field(default_factory=list)
    artifact_digest: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None
    completed_at: datetime | None = None
