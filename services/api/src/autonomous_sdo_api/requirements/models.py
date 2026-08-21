from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class VerificationMethod(StrEnum):
    AUTOMATED_TEST = "automated_test"
    MANUAL_CHECK = "manual_check"
    CONTRACT_VERIFICATION = "contract_verification"
    SECURITY_SCAN = "security_scan"


class AcceptanceCriterion(BaseModel):
    """Verifiable condition for requirement acceptance."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    criterion_text: str = Field(min_length=1)
    verification_method: VerificationMethod = VerificationMethod.AUTOMATED_TEST
    is_mandatory: bool = True


class RequirementStatus(StrEnum):
    DRAFT = "draft"
    PENDING_CLARIFICATION = "pending_clarification"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SUPERSEDED = "superseded"


class RequirementRevision(BaseModel):
    """Immutable snapshot of a requirement revision."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    requirement_id: str = Field(min_length=1)
    version: int = Field(gt=0)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    scope: str = ""
    acceptance_criteria: list[AcceptanceCriterion] = Field(default_factory=list)
    status: RequirementStatus
    author_id: str = Field(min_length=1)
    created_at: datetime


class ClarificationStatus(StrEnum):
    PENDING = "pending"
    RESOLVED = "resolved"


class ClarificationRequest(BaseModel):
    """Interactive clarification question with optional predefined choices."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    requirement_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    options: list[str] = Field(default_factory=list)
    response: str | None = None
    status: ClarificationStatus = ClarificationStatus.PENDING
    created_at: datetime
    resolved_at: datetime | None = None


class CreateRequirementRequest(BaseModel):
    """Payload to create a new requirement with initial acceptance criteria."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    scope: str = ""
    acceptance_criteria: list[AcceptanceCriterion] = Field(min_length=1)


class CreateRevisionRequest(BaseModel):
    """Payload to evolve an existing requirement into a new immutable version."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    scope: str = ""
    acceptance_criteria: list[AcceptanceCriterion] = Field(min_length=1)


class RequestClarificationPayload(BaseModel):
    """Payload to ask a clarification question."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    question: str = Field(min_length=1)
    options: list[str] = Field(default_factory=list)


class ResolveClarificationRequest(BaseModel):
    """Payload to provide an answer to a pending clarification."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    response: str = Field(min_length=1)


class RequirementError(Exception):
    """Base requirements domain error."""


class RequirementNotFoundError(RequirementError):
    """Requirement or revision was not found in the tenant workspace."""


class ClarificationNotFoundError(RequirementError):
    """Clarification request was not found."""
