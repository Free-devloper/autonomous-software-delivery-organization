"""Review service with approval engine, threading, and staleness controls."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from autonomous_sdo_api.reviews.models import (
    PrProvider,
    PullRequestModel,
    PullRequestState,
    ReviewApprovalModel,
    ReviewComment,
    compute_pr_digest,
)


class ReviewService:
    """In-memory review service with digest-bound approvals and staleness."""

    def __init__(self) -> None:
        self._pull_requests: dict[str, PullRequestModel] = {}

    def create_pull_request(
        self,
        *,
        organization_id: UUID,
        provider: str,
        repository: str,
        title: str,
        description: str = "",
        source_branch: str,
        target_branch: str,
        head_sha: str,
        author_id: str,
    ) -> PullRequestModel:
        """Create a new pull request."""
        pr = PullRequestModel(
            id=f"pr-{uuid4().hex[:12]}",
            organization_id=organization_id,
            provider=PrProvider(provider),
            repository=repository,
            pr_number=len(self._pull_requests) + 1,
            title=title,
            description=description,
            source_branch=source_branch,
            target_branch=target_branch,
            head_sha=head_sha,
            author_id=author_id,
        )
        self._pull_requests[pr.id] = pr
        return pr

    def get_pull_request(self, pr_id: str, organization_id: UUID) -> PullRequestModel | None:
        """Retrieve a PR by ID and organization (tenant-isolated)."""
        pr = self._pull_requests.get(pr_id)
        if pr and pr.organization_id == organization_id:
            return pr
        return None

    def list_pull_requests(self, organization_id: UUID) -> list[PullRequestModel]:
        """List all PRs for an organization."""
        return [pr for pr in self._pull_requests.values() if pr.organization_id == organization_id]

    def add_comment(
        self,
        pr_id: str,
        organization_id: UUID,
        *,
        author_id: str,
        file_path: str,
        line_number: int,
        body: str,
        parent_id: str | None = None,
    ) -> ReviewComment | None:
        """Add a threaded comment to a PR."""
        pr = self.get_pull_request(pr_id, organization_id)
        if not pr:
            return None
        comment = ReviewComment(
            id=f"c-{uuid4().hex[:12]}",
            review_id=pr_id,
            author_id=author_id,
            file_path=file_path,
            line_number=line_number,
            body=body,
            parent_id=parent_id,
        )
        pr.comments.append(comment)
        return comment

    def resolve_comment(self, pr_id: str, organization_id: UUID, comment_id: str) -> bool:
        """Mark a comment as resolved."""
        pr = self.get_pull_request(pr_id, organization_id)
        if not pr:
            return False
        for comment in pr.comments:
            if comment.id == comment_id:
                comment.resolved = True
                comment.updated_at = datetime.now(UTC)
                return True
        return False

    def submit_approval(
        self,
        pr_id: str,
        organization_id: UUID,
        *,
        approver_id: str,
        artifact_digest: str,
        scope: str,
        environment: str,
        expires_in_hours: int = 24,
    ) -> ReviewApprovalModel | None:
        """Submit a digest-bound approval with separation of duties check."""
        pr = self.get_pull_request(pr_id, organization_id)
        if not pr:
            return None

        # Separation of duties: author cannot approve own PR
        if approver_id == pr.author_id:
            return None

        # Check for replayed/duplicate approvals
        for existing in pr.approvals:
            if (
                existing.approver_id == approver_id
                and existing.artifact_digest == artifact_digest
                and not existing.is_stale
                and not existing.is_expired()
            ):
                return None

        approval = ReviewApprovalModel(
            id=f"a-{uuid4().hex[:12]}",
            review_id=pr_id,
            approver_id=approver_id,
            artifact_digest=artifact_digest,
            scope=scope,
            environment=environment,
            expires_at=datetime.now(UTC) + timedelta(hours=expires_in_hours),
        )
        pr.approvals.append(approval)
        return approval

    def check_staleness(self, pr_id: str, organization_id: UUID) -> int:
        """Invalidate stale approvals whose digest no longer matches HEAD."""
        pr = self.get_pull_request(pr_id, organization_id)
        if not pr:
            return 0
        current_digest = compute_pr_digest(pr)
        stale_count = 0
        for approval in pr.approvals:
            if approval.invalidate_if_stale(current_digest):
                stale_count += 1
        return stale_count

    def merge_pull_request(self, pr_id: str, organization_id: UUID) -> PullRequestModel | None:
        """Merge a PR if it has valid approvals with separation of duties."""
        pr = self.get_pull_request(pr_id, organization_id)
        if not pr:
            return None
        if pr.state != PullRequestState.OPEN:
            return None
        active = pr.active_approvals()
        if not active:
            return None
        if not pr.has_separation_of_duties():
            return None
        pr.state = PullRequestState.MERGED
        pr.merged_at = datetime.now(UTC)
        return pr
