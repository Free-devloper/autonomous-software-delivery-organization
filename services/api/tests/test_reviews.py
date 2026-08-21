"""Tests for the review & pull request subsystem."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from autonomous_sdo_api.reviews.models import (
    PrProvider,
    PullRequestModel,
    PullRequestState,
    ReviewApprovalModel,
    ReviewComment,
    ReviewStatus,
    compute_pr_digest,
)
from autonomous_sdo_api.reviews.service import ReviewService

pytestmark = pytest.mark.unit

ORG_ID = UUID("00000000-0000-0000-0000-000000000001")
OTHER_ORG = UUID("00000000-0000-0000-0000-000000000002")


class TestReviewModels:
    def test_review_comment_creation(self) -> None:
        comment = ReviewComment(
            id="c-001",
            review_id="r-001",
            author_id="u-001",
            file_path="src/main.py",
            line_number=42,
            body="Needs a test",
        )
        assert comment.resolved is False
        assert comment.parent_id is None

    def test_approval_expiry(self) -> None:
        approval = ReviewApprovalModel(
            id="a-001",
            review_id="r-001",
            approver_id="u-002",
            artifact_digest="a" * 64,
            scope="deploy",
            environment="production",
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
        assert approval.is_expired() is True

    def test_approval_not_expired(self) -> None:
        approval = ReviewApprovalModel(
            id="a-002",
            review_id="r-001",
            approver_id="u-002",
            artifact_digest="b" * 64,
            scope="deploy",
            environment="staging",
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
        assert approval.is_expired() is False

    def test_staleness_invalidation(self) -> None:
        approval = ReviewApprovalModel(
            id="a-003",
            review_id="r-001",
            approver_id="u-002",
            artifact_digest="c" * 64,
            scope="deploy",
            environment="staging",
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
        # Different digest should mark stale
        assert approval.invalidate_if_stale("d" * 64) is True
        assert approval.is_stale is True
        assert approval.status == ReviewStatus.EXPIRED

    def test_separation_of_duties(self) -> None:
        pr = PullRequestModel(
            id="pr-001",
            organization_id=ORG_ID,
            provider=PrProvider.GITHUB,
            repository="org/repo",
            pr_number=1,
            title="test",
            source_branch="feature",
            target_branch="main",
            head_sha="abc123",
            author_id="u-001",
        )
        # No approvals → separation OK
        assert pr.has_separation_of_duties() is True

        # Author approves own PR → violation
        pr.approvals.append(
            ReviewApprovalModel(
                id="a-100",
                review_id="pr-001",
                approver_id="u-001",
                artifact_digest="e" * 64,
                scope="deploy",
                environment="prod",
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
        assert pr.has_separation_of_duties() is False

    def test_compute_pr_digest_deterministic(self) -> None:
        pr = PullRequestModel(
            id="pr-001",
            organization_id=ORG_ID,
            provider=PrProvider.GITHUB,
            repository="org/repo",
            pr_number=1,
            title="test",
            source_branch="feature",
            target_branch="main",
            head_sha="abc123",
            author_id="u-001",
        )
        d1 = compute_pr_digest(pr)
        d2 = compute_pr_digest(pr)
        assert d1 == d2
        assert len(d1) == 64


class TestReviewService:
    def test_create_and_list_prs(self) -> None:
        svc = ReviewService()
        pr = svc.create_pull_request(
            organization_id=ORG_ID,
            provider="github",
            repository="org/repo",
            title="feat: test",
            source_branch="feature/x",
            target_branch="main",
            head_sha="abc",
            author_id="u-001",
        )
        assert pr.state == PullRequestState.OPEN
        prs = svc.list_pull_requests(ORG_ID)
        assert len(prs) == 1

    def test_tenant_isolation(self) -> None:
        svc = ReviewService()
        svc.create_pull_request(
            organization_id=ORG_ID,
            provider="github",
            repository="org/repo",
            title="test",
            source_branch="f",
            target_branch="m",
            head_sha="x",
            author_id="u-001",
        )
        # Other org should see nothing
        assert len(svc.list_pull_requests(OTHER_ORG)) == 0

    def test_add_threaded_comment(self) -> None:
        svc = ReviewService()
        pr = svc.create_pull_request(
            organization_id=ORG_ID,
            provider="github",
            repository="org/repo",
            title="test",
            source_branch="f",
            target_branch="m",
            head_sha="x",
            author_id="u-001",
        )
        comment = svc.add_comment(
            pr.id,
            ORG_ID,
            author_id="u-002",
            file_path="src/main.py",
            line_number=10,
            body="Add test",
        )
        assert comment is not None
        reply = svc.add_comment(
            pr.id,
            ORG_ID,
            author_id="u-001",
            file_path="src/main.py",
            line_number=10,
            body="Done",
            parent_id=comment.id,
        )
        assert reply is not None
        assert reply.parent_id == comment.id

    def test_self_approval_rejected(self) -> None:
        svc = ReviewService()
        pr = svc.create_pull_request(
            organization_id=ORG_ID,
            provider="github",
            repository="org/repo",
            title="test",
            source_branch="f",
            target_branch="m",
            head_sha="x",
            author_id="u-001",
        )
        # Author trying to approve own PR
        result = svc.submit_approval(
            pr.id,
            ORG_ID,
            approver_id="u-001",
            artifact_digest="a" * 64,
            scope="deploy",
            environment="prod",
        )
        assert result is None

    def test_valid_approval_and_merge(self) -> None:
        svc = ReviewService()
        pr = svc.create_pull_request(
            organization_id=ORG_ID,
            provider="github",
            repository="org/repo",
            title="test",
            source_branch="f",
            target_branch="m",
            head_sha="x",
            author_id="u-001",
        )
        approval = svc.submit_approval(
            pr.id,
            ORG_ID,
            approver_id="u-002",
            artifact_digest="b" * 64,
            scope="deploy",
            environment="staging",
        )
        assert approval is not None
        merged = svc.merge_pull_request(pr.id, ORG_ID)
        assert merged is not None
        assert merged.state == PullRequestState.MERGED

    def test_merge_without_approval_fails(self) -> None:
        svc = ReviewService()
        pr = svc.create_pull_request(
            organization_id=ORG_ID,
            provider="github",
            repository="org/repo",
            title="test",
            source_branch="f",
            target_branch="m",
            head_sha="x",
            author_id="u-001",
        )
        result = svc.merge_pull_request(pr.id, ORG_ID)
        assert result is None

    def test_staleness_check(self) -> None:
        svc = ReviewService()
        pr = svc.create_pull_request(
            organization_id=ORG_ID,
            provider="github",
            repository="org/repo",
            title="test",
            source_branch="f",
            target_branch="m",
            head_sha="x",
            author_id="u-001",
        )
        svc.submit_approval(
            pr.id,
            ORG_ID,
            approver_id="u-002",
            artifact_digest="c" * 64,
            scope="deploy",
            environment="staging",
        )
        # All approvals with non-matching digest should be stale
        stale = svc.check_staleness(pr.id, ORG_ID)
        assert stale == 1

    def test_resolve_comment(self) -> None:
        svc = ReviewService()
        pr = svc.create_pull_request(
            organization_id=ORG_ID,
            provider="github",
            repository="org/repo",
            title="test",
            source_branch="f",
            target_branch="m",
            head_sha="x",
            author_id="u-001",
        )
        comment = svc.add_comment(
            pr.id,
            ORG_ID,
            author_id="u-002",
            file_path="src/main.py",
            line_number=5,
            body="Fix this",
        )
        assert comment is not None
        assert svc.resolve_comment(pr.id, ORG_ID, comment.id) is True
        resolved_pr = svc.get_pull_request(pr.id, ORG_ID)
        assert resolved_pr is not None
        assert resolved_pr.comments[0].resolved is True


class TestReviewRoutes:
    def _make_client(self, org_id: str | None = None, user_id: str | None = None) -> TestClient:
        from autonomous_sdo_api.app import create_app
        from autonomous_sdo_api.config import Settings
        from autonomous_sdo_api.database.tenancy import (
            OrganizationContext,
            get_organization_context,
        )
        from autonomous_sdo_api.policy import Role

        settings = Settings(
            service_name="test",
            database_url=None,
            oidc_issuer=None,
            oidc_audience=None,
            oidc_jwks=None,
        )
        app = create_app(settings)
        _org = UUID(org_id) if org_id else uuid4()
        _user = user_id or str(uuid4())
        app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
            organization_id=_org,
            actor_id=_user,
            roles=frozenset({Role.REPOSITORY_MAINTAINER}),
        )
        return TestClient(app)

    def test_create_pr_route(self) -> None:
        org_id = str(uuid4())
        client = self._make_client(org_id=org_id)
        resp = client.post(
            "/api/v1/reviews/pull-requests",
            json={
                "provider": "github",
                "repository": "org/repo",
                "title": "feat: test",
                "source_branch": "feature/x",
                "target_branch": "main",
                "head_sha": "abc",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "feat: test"
        assert data["state"] == "open"

    def test_list_prs_route(self) -> None:
        client = self._make_client()
        org_id = str(uuid4())
        user_id = str(uuid4())
        headers = {
            "x-organization-id": org_id,
            "x-user-id": user_id,
            "x-roles": "admin",
        }
        client.post(
            "/api/v1/reviews/pull-requests",
            json={
                "provider": "github",
                "repository": "org/repo",
                "title": "test",
                "source_branch": "f",
                "target_branch": "m",
                "head_sha": "x",
            },
            headers=headers,
        )
        resp = client.get("/api/v1/reviews/pull-requests", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1
