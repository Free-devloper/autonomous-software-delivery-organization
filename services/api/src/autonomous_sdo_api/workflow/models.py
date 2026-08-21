from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from autonomous_sdo_api.events.models import WorkflowNode as WorkflowNode


class WorkflowState(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowCheckpoint(BaseModel):
    """Immutable state checkpoint of a durable workflow run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    workflow_id: str = Field(min_length=1)
    step_index: int = Field(ge=0)
    node_name: WorkflowNode
    state_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class WorkflowExecution(BaseModel):
    """Active instance of a durable workflow execution."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    requirement_id: str = Field(min_length=1)
    plan_id: str | None = None
    current_node: WorkflowNode
    state: WorkflowState
    step_count: int = Field(ge=0)
    actor_id: str = Field(min_length=1)
    created_at: datetime
    updated_at: datetime


class StartWorkflowRequest(BaseModel):
    """Payload to start a durable workflow execution."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    requirement_id: str = Field(min_length=1)
    plan_id: str | None = None
    initial_payload: dict[str, Any] = Field(default_factory=dict)


class SignalWorkflowRequest(BaseModel):
    """Signal payload sent to a workflow."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    signal_name: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class RollbackWorkflowRequest(BaseModel):
    """Payload to roll back a workflow to a specific checkpoint."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    checkpoint_id: str = Field(min_length=1)


class WorkflowError(Exception):
    """Base workflow domain exception."""


class WorkflowNotFoundError(WorkflowError):
    """Workflow execution instance not found."""


class CheckpointNotFoundError(WorkflowError):
    """Workflow checkpoint not found."""


class InvalidWorkflowStateTransitionError(WorkflowError):
    """Invalid workflow state transition."""
