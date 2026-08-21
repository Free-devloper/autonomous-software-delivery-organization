from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WorkflowNode(StrEnum):
    REQUIREMENTS_ANALYSIS = "requirements_analysis"
    PLANNING_AND_BUDGET = "planning_and_budget"
    AWAITING_HUMAN_APPROVAL = "awaiting_human_approval"
    EXECUTION_DISPATCH = "execution_dispatch"
    VERIFICATION_AND_TESTING = "verification_and_testing"
    REVIEW_AND_SIGNOFF = "review_and_signoff"


class WorkflowEventType(StrEnum):
    NODE_TRANSITION = "node_transition"
    TOKEN_USAGE = "token_usage"
    AGENT_MESSAGE = "agent_message"
    APPROVAL_REQUESTED = "approval_requested"
    STATUS_CHANGE = "status_change"


class WorkflowEvent(BaseModel):
    """Event payload emitted during workflow execution."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    workflow_id: str = Field(min_length=1)
    event_type: WorkflowEventType
    node_name: WorkflowNode
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime
