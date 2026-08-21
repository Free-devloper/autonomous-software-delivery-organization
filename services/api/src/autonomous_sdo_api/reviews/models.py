"""Domain models for code reviews, approvals, and pull requests."""

from __future__ import annotations

import enum
import hashlib
from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReviewStatus(enum.StrEnum):
    """Review lifecycle states."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    DISMISSED = "dismissed"
    EXPIRED = "expired"


class PullRequestState(enum.StrEnum):
    """Pull request lifecycle states."""

    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"
    DRAFT = "draft"


class PrProvider(enum.StrEnum):
    """SCM provider enum."""

    GITHUB = "github"
    GITLAB = "gitlab"


class ReviewComment(BaseModel):
    """A threaded review comment anchored to a file location."""

    id: str
    review_id: str
    author_id: str
    file_path: str
    line_number: int = Field(ge=0)
    body: str
    parent_id: str | None = None
    resolved: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None


class ReviewApprovalModel(BaseModel):
    """Digest-bound approval with expiry and separation of duties."""

    id: str
    review_id: str
    approver_id: str
    artifact_digest: str = Field(min_length=64, max_length=64)
    scope: str
    environment: str
    status: ReviewStatus = ReviewStatus.APPROVED
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_stale: bool = False

    def is_expired(self) -> bool:
        """Check whether this approval has passed its expiry time."""
        return datetime.now(UTC) > self.expires_at

    def invalidate_if_stale(self, current_digest: str) -> bool:
        """Mark stale if artifact digest no longer matches."""
        if self.artifact_digest != current_digest:
            self.is_stale = True
            self.status = ReviewStatus.EXPIRED
        return self.is_stale


class PullRequestModel(BaseModel):
    """Domain model for a pull request with review state."""

    id: str
    organization_id: UUID
    provider: PrProvider
    repository: str
    pr_number: int = Field(gt=0)
    title: str
    description: str = ""
    source_branch: str
    target_branch: str
    state: PullRequestState = PullRequestState.OPEN
    author_id: str
    head_sha: str
    approvals: list[ReviewApprovalModel] = Field(default_factory=list)
    comments: list[ReviewComment] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None
    merged_at: datetime | None = None

    def has_separation_of_duties(self) -> bool:
        """Verify no approver is the PR author (separation of duties)."""
        return all(a.approver_id != self.author_id for a in self.approvals)

    def active_approvals(self) -> list[ReviewApprovalModel]:
        """Return non-stale, non-expired approvals."""
        return [
            a
            for a in self.approvals
            if not a.is_stale and not a.is_expired() and a.status == ReviewStatus.APPROVED
        ]


def compute_pr_digest(pr: PullRequestModel) -> str:
    """Compute a deterministic digest from PR content."""
    content = f"{pr.head_sha}:{pr.source_branch}:{pr.target_branch}:{pr.pr_number}"
    return hashlib.sha256(content.encode()).hexdigest()
