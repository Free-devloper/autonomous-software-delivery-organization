"""Domain models for security scanning, testing, and quality gates."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FindingSeverity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class ScanToolCategory(StrEnum):
    SAST = "sast"
    DEPENDENCY = "dependency"
    SECRET = "secret"
    CONTAINER = "container"
    IAC = "iac"
    LICENSE = "license"


class SecurityFinding(BaseModel):
    """Single SARIF-compatible security finding."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    rule_id: str = Field(min_length=1)
    tool: str = Field(min_length=1)
    category: ScanToolCategory
    severity: FindingSeverity
    message: str = Field(min_length=1)
    file_path: str = Field(min_length=1)
    start_line: int = Field(ge=0)
    end_line: int | None = None
    snippet: str | None = None
    cwe_ids: list[str] = Field(default_factory=list)
    fix_suggestion: str | None = None
    suppressed: bool = False


class SecurityScanReport(BaseModel):
    """Aggregated security scan report for a target."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    organization_id: UUID
    scan_target: str = Field(min_length=1)
    tool_name: str = Field(min_length=1)
    tool_version: str = Field(min_length=1)
    category: ScanToolCategory
    findings: list[SecurityFinding] = Field(default_factory=list)
    total_findings: int = Field(ge=0)
    critical_count: int = Field(ge=0)
    high_count: int = Field(ge=0)
    passed: bool
    scanned_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TestStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    FLAKY = "flaky"


class TestCaseResult(BaseModel):
    """Single test case execution result."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    suite: str = Field(min_length=1)
    file_path: str = Field(min_length=1)
    status: TestStatus
    duration_ms: float = Field(ge=0)
    error_message: str | None = None
    retry_count: int = Field(default=0, ge=0)
    is_flaky: bool = False


class CoverageEntry(BaseModel):
    """Coverage for a single source file."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    file_path: str = Field(min_length=1)
    statement_coverage: float = Field(ge=0, le=100)
    branch_coverage: float = Field(ge=0, le=100)
    function_coverage: float = Field(ge=0, le=100)
    line_coverage: float = Field(ge=0, le=100)
    uncovered_lines: list[int] = Field(default_factory=list)


class TestSuiteReport(BaseModel):
    """Aggregated test suite execution report."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    organization_id: UUID
    suite_name: str = Field(min_length=1)
    total_tests: int = Field(ge=0)
    passed: int = Field(ge=0)
    failed: int = Field(ge=0)
    skipped: int = Field(ge=0)
    flaky: int = Field(ge=0)
    duration_ms: float = Field(ge=0)
    coverage: list[CoverageEntry] = Field(default_factory=list)
    test_results: list[TestCaseResult] = Field(default_factory=list)
    overall_passed: bool
    run_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MutationReport(BaseModel):
    """Mutation testing summary with pass/fail threshold."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    organization_id: UUID
    total_mutants: int = Field(ge=0)
    killed: int = Field(ge=0)
    survived: int = Field(ge=0)
    timeout: int = Field(ge=0)
    no_coverage: int = Field(ge=0)
    mutation_score: float = Field(ge=0, le=100)
    threshold: float = Field(ge=0, le=100)
    passed: bool
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class QualityGateStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


class QualityGateCheck(BaseModel):
    """Individual quality gate check result."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    status: QualityGateStatus
    threshold: str = Field(min_length=1)
    actual: str = Field(min_length=1)
    message: str | None = None


class QualityGateEvaluation(BaseModel):
    """Combined quality gate evaluation for a work package."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    organization_id: UUID
    work_package_id: str = Field(min_length=1)
    overall_status: QualityGateStatus
    checks: list[QualityGateCheck] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def compute_scan_digest(
    tool_name: str,
    scan_target: str,
    findings: list[SecurityFinding],
) -> str:
    """Deterministic SHA-256 digest for scan reproducibility."""
    canonical = json.dumps(
        {
            "tool": tool_name,
            "target": scan_target,
            "findings": sorted(
                [f.model_dump(mode="json") for f in findings],
                key=lambda x: (x["file_path"], x["start_line"]),
            ),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode()).hexdigest()
