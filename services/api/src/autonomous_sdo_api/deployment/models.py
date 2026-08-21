"""Data models for deployment and rollback subsystems."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class ReleaseStrategy(StrEnum):
    ROLLING = "rolling"
    CANARY = "canary"
    BLUE_GREEN = "blue_green"


class DeploymentEnvironment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DeploymentStatus(StrEnum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    CANARY_VALIDATING = "canary_validating"
    PROMOTED = "promoted"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLBACK_PENDING_APPROVAL = "rollback_pending_approval"
    ROLLBACK_APPROVED = "rollback_approved"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"


class MigrationRiskLevel(StrEnum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BREAKING = "breaking"


class ExpandContractStep(StrEnum):
    EXPAND = "expand"
    MIGRATE = "migrate"
    CONTRACT = "contract"
    STANDALONE = "standalone"


class SchemaMigrationPlanModel(BaseModel):
    """Represents a database migration tied to a release."""

    id: str
    migration_name: str
    version: str
    is_backward_compatible: bool = True
    expand_contract_step: ExpandContractStep = ExpandContractStep.EXPAND
    estimated_duration_seconds: int = 30
    risk_level: MigrationRiskLevel = MigrationRiskLevel.LOW
    rollback_sql: str | None = None


class DeploymentApprovalPurpose(StrEnum):
    DEPLOY = "deploy"
    ROLLBACK = "rollback"


class DeploymentApprovalModel(BaseModel):
    """Digest-bound and purpose-separated approval for deploy or rollback."""

    id: str
    plan_id: str
    approver_id: str
    purpose: DeploymentApprovalPurpose
    artifact_digest: str
    environment: DeploymentEnvironment
    approved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime
    notes: str = ""

    def is_expired(self) -> bool:
        return datetime.now(UTC) > self.expires_at

    def is_digest_valid(self, current_digest: str) -> bool:
        return self.artifact_digest == current_digest


class SloGateMetricModel(BaseModel):
    """SLO check used to gate canary promotion."""

    metric_name: str
    target_value: float
    actual_value: float
    passed: bool
    unit: str


class PostRollbackCheckModel(BaseModel):
    """Post-rollback automated health check result."""

    check_name: str
    passed: bool
    details: str
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ReleasePlanModel(BaseModel):
    """Complete release deployment specification."""

    id: str
    organization_id: UUID
    title: str
    version: str
    artifact_digest: str
    artifact_image: str
    strategy: ReleaseStrategy = ReleaseStrategy.ROLLING
    target_environment: DeploymentEnvironment = DeploymentEnvironment.STAGING
    status: DeploymentStatus = DeploymentStatus.DRAFT
    migrations: list[SchemaMigrationPlanModel] = Field(default_factory=list)
    canary_weight_percentage: int = 10
    canary_duration_seconds: int = 300
    slo_gates: list[SloGateMetricModel] = Field(default_factory=list)
    deploy_approvals: list[DeploymentApprovalModel] = Field(default_factory=list)
    rollback_approvals: list[DeploymentApprovalModel] = Field(default_factory=list)
    post_rollback_checks: list[PostRollbackCheckModel] = Field(default_factory=list)
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None
    completed_at: datetime | None = None
