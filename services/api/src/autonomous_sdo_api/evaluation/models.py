"""Data models for evaluation, cost analytics, and disaster recovery."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class EvaluationCategory(StrEnum):
    CORRECTNESS = "correctness"
    SECURITY_RECALL = "security_recall"
    PERFORMANCE_SLO = "performance_slo"
    MUTATION_SCORE = "mutation_score"
    FLAKE_RATE = "flake_rate"
    COST_EFFICIENCY = "cost_efficiency"
    RECOVERY_READINESS = "recovery_readiness"


class EvaluationStatus(StrEnum):
    RUNNING = "running"
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


class MetricScoreModel(BaseModel):
    """Specific metric evaluated against defined thresholds."""

    name: str
    category: EvaluationCategory
    score: float
    target_threshold: float
    passed: bool
    unit: str
    details: str = ""


class EvaluationReportModel(BaseModel):
    """Holistic production-readiness evaluation report."""

    id: str
    organization_id: UUID
    run_id: str
    overall_status: EvaluationStatus
    summary: str
    metrics: list[MetricScoreModel] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    evaluation_window_hours: int = 24


class TokenCostMetricModel(BaseModel):
    """Breakdown of token usage per model provider."""

    model_name: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class CostReportModel(BaseModel):
    """Cost and quota tracking report."""

    id: str
    organization_id: UUID
    period_start: datetime
    period_end: datetime
    total_cost_usd: float
    budget_limit_usd: float
    budget_consumed_percentage: float
    is_within_budget: bool
    model_breakdown: list[TokenCostMetricModel] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BackupType(StrEnum):
    DATABASE = "database"
    VECTOR_INDEX = "vector_index"
    AUDIT_LOG = "audit_log"
    FULL = "full"


class BackupStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class BackupJobModel(BaseModel):
    """Disaster recovery backup snapshot."""

    id: str
    organization_id: UUID
    backup_type: BackupType = BackupType.FULL
    status: BackupStatus = BackupStatus.PENDING
    storage_uri: str
    artifact_digest: str
    size_bytes: int = 0
    rpo_target_minutes: int = 15
    rto_target_minutes: int = 60
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None


class RestoreJobModel(BaseModel):
    """Disaster recovery restore verification drill."""

    id: str
    organization_id: UUID
    backup_id: str
    status: BackupStatus = BackupStatus.PENDING
    observed_recovery_time_seconds: int | None = None
    data_integrity_verified: bool = False
    verified_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
