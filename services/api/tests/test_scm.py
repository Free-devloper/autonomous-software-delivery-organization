import hashlib
import hmac
from datetime import UTC, datetime

import httpx
import pytest
from pydantic import ValidationError

from autonomous_sdo_api.scm import (
    CommitResolution,
    GitHubAdapter,
    GitLabAdapter,
    RepositoryDescriptor,
    RepositoryVisibility,
    ScmAuthenticationError,
    ScmError,
    ScmNotFoundError,
    ScmProvider,
    ScmRateLimitError,
    WebhookEventType,
    get_scm_adapter,
    normalize_github_webhook,
    normalize_gitlab_webhook,
    verify_github_signature,
    verify_gitlab_token,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Model Tests
# ---------------------------------------------------------------------------


def test_repository_descriptor_valid() -> None:
    repo = RepositoryDescriptor(
        provider=ScmProvider.GITHUB,
        id="12345",
        owner="roytechworkforce",
        name="asdo",
        full_name="roytechworkforce/asdo",
        default_branch="main",
        visibility=RepositoryVisibility.PRIVATE,
        clone_url_http="https://github.com/roytechworkforce/asdo.git",
        clone_url_ssh="git@github.com:roytechworkforce/asdo.git",
        is_archived=False,
    )
    assert repo.full_name == "roytechworkforce/asdo"
    assert repo.visibility == RepositoryVisibility.PRIVATE


def test_commit_resolution_sha_validation() -> None:
    valid_sha1 = "a" * 40
    valid_sha256 = "b" * 64
    now = datetime.now(UTC)

    commit1 = CommitResolution(
        provider=ScmProvider.GITHUB,
        repository_id="roytechworkforce/asdo",
        commit_sha=valid_sha1,
        message="init",
        author_name="Dev",
        author_email="dev@example.com",
        authored_at=now,
        parent_shas=[],
    )
    assert commit1.commit_sha == valid_sha1

    commit2 = CommitResolution(
        provider=ScmProvider.GITLAB,
        repository_id="roytechworkforce/asdo",
        commit_sha=valid_sha256,
        message="init sha256",
        author_name="Dev",
        author_email="dev@example.com",
        authored_at=now,
        parent_shas=[valid_sha256],
    )
    assert commit2.commit_sha == valid_sha256

    with pytest.raises(ValidationError):
        CommitResolution(
            provider=ScmProvider.GITHUB,
            repository_id="roytechworkforce/asdo",
            commit_sha="invalid-sha",
            message="bad",
            author_name="Dev",
            author_email="dev@example.com",
            authored_at=now,
        )


# ---------------------------------------------------------------------------
# GitHub Adapter Tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_github_adapter_get_repository() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/roytechworkforce/asdo"
        assert request.headers.get("Authorization") == "Bearer test-gh-token"
        return httpx.Response(
            200,
            json={
                "id": 98765,
                "name": "asdo",
                "full_name": "roytechworkforce/asdo",
                "owner": {"login": "roytechworkforce"},
                "default_branch": "main",
                "private": True,
                "visibility": "private",
                "clone_url": "https://github.com/roytechworkforce/asdo.git",
                "ssh_url": "git@github.com:roytechworkforce/asdo.git",
                "archived": False,
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as client:
        adapter = GitHubAdapter(token="test-gh-token", client=client)
        repo = await adapter.get_repository("roytechworkforce", "asdo")

        assert repo.provider == ScmProvider.GITHUB
        assert repo.id == "98765"
        assert repo.owner == "roytechworkforce"
        assert repo.name == "asdo"
        assert repo.default_branch == "main"
        assert repo.visibility == RepositoryVisibility.PRIVATE
        assert repo.is_archived is False


@pytest.mark.anyio
async def test_github_adapter_resolve_commit() -> None:
    sha = "1" * 40
    parent_sha = "0" * 40

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/roytechworkforce/asdo/commits/main"
        return httpx.Response(
            200,
            json={
                "sha": sha,
                "commit": {
                    "message": "feat: autonomous core",
                    "author": {
                        "name": "Roy Engine",
                        "email": "engine@roytech.org",
                        "date": "2026-08-19T10:00:00Z",
                    },
                },
                "parents": [{"sha": parent_sha}],
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as client:
        adapter = GitHubAdapter(token="test-token", client=client)
        commit = await adapter.resolve_commit("roytechworkforce", "asdo", "main")

        assert commit.commit_sha == sha
        assert commit.author_name == "Roy Engine"
        assert commit.parent_shas == [parent_sha]
        assert commit.ref_requested == "main"


@pytest.mark.anyio
async def test_github_adapter_get_file_content_and_branches() -> None:
    sha = "1" * 40

    async def handler(request: httpx.Request) -> httpx.Response:
        if "/contents/README.md" in request.url.path:
            assert request.url.params.get("ref") == sha
            return httpx.Response(200, content=b"# ASDO Platform")
        if "/branches" in request.url.path:
            return httpx.Response(200, json=[{"name": "main"}, {"name": "develop"}])
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as client:
        adapter = GitHubAdapter(token="token", client=client)
        content = await adapter.get_file_content("roytechworkforce", "asdo", sha, "README.md")
        assert content == b"# ASDO Platform"

        branches = await adapter.list_branches("roytechworkforce", "asdo")
        assert branches == ["main", "develop"]


@pytest.mark.anyio
async def test_github_adapter_errors() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if "/repos/err/401" in request.url.path:
            return httpx.Response(401, text="Bad credentials")
        if "/repos/err/ratelimit" in request.url.path:
            return httpx.Response(
                403,
                text="rate limit",
                headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1700000000"},
            )
        if "/repos/err/404" in request.url.path:
            return httpx.Response(404, text="Not Found")
        return httpx.Response(500, text="Internal Server Error")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as client:
        adapter = GitHubAdapter(token="token", client=client)

        with pytest.raises(ScmAuthenticationError):
            await adapter.get_repository("err", "401")

        with pytest.raises(ScmRateLimitError) as exc_info:
            await adapter.get_repository("err", "ratelimit")
        assert exc_info.value.reset_epoch == 1700000000

        with pytest.raises(ScmNotFoundError):
            await adapter.get_repository("err", "404")

        with pytest.raises(ScmError):
            await adapter.get_repository("err", "500")


# ---------------------------------------------------------------------------
# GitLab Adapter Tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_gitlab_adapter_get_repository_and_commits() -> None:
    sha = "2" * 40
    parent_sha = "1" * 40

    async def handler(request: httpx.Request) -> httpx.Response:
        raw_path = request.url.raw_path.decode("utf-8")
        if "/repository/commits/main" in raw_path:
            return httpx.Response(
                200,
                json={
                    "id": sha,
                    "message": "gitlab commit",
                    "author_name": "GL Dev",
                    "author_email": "gldev@roytech.org",
                    "authored_date": "2026-08-19T11:00:00Z",
                    "parent_ids": [parent_sha],
                },
            )
        if (
            "/repository/files/src%2Fmain.py/raw" in raw_path
            or "/files/src/main.py/raw" in request.url.path
        ):
            assert request.url.params.get("ref") == sha
            return httpx.Response(200, content=b"print('hello')")
        if "/repository/branches" in raw_path:
            return httpx.Response(200, json=[{"name": "main"}, {"name": "feature"}])
        if "/projects/" in raw_path:
            assert request.headers.get("PRIVATE-TOKEN") == "test-gl-token"
            return httpx.Response(
                200,
                json={
                    "id": 54321,
                    "name": "asdo",
                    "path_with_namespace": "roytechworkforce/asdo",
                    "namespace": {"full_path": "roytechworkforce"},
                    "default_branch": "main",
                    "visibility": "internal",
                    "http_url_to_repo": "https://gitlab.com/roytechworkforce/asdo.git",
                    "ssh_url_to_repo": "git@gitlab.com:roytechworkforce/asdo.git",
                    "archived": False,
                },
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        transport=transport, base_url="https://gitlab.com/api/v4"
    ) as client:
        adapter = GitLabAdapter(token="test-gl-token", client=client)
        repo = await adapter.get_repository("roytechworkforce", "asdo")

        assert repo.provider == ScmProvider.GITLAB
        assert repo.id == "54321"
        assert repo.visibility == RepositoryVisibility.INTERNAL

        commit = await adapter.resolve_commit("roytechworkforce", "asdo", "main")
        assert commit.commit_sha == sha
        assert commit.parent_shas == [parent_sha]

        content = await adapter.get_file_content("roytechworkforce", "asdo", sha, "src/main.py")
        assert content == b"print('hello')"

        branches = await adapter.list_branches("roytechworkforce", "asdo")
        assert branches == ["main", "feature"]


@pytest.mark.anyio
async def test_gitlab_adapter_errors() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if "/401" in request.url.path:
            return httpx.Response(401, text="Unauthorized")
        if "/429" in request.url.path:
            return httpx.Response(429, text="Too Many Requests")
        if "/404" in request.url.path:
            return httpx.Response(404, text="404 Project Not Found")
        return httpx.Response(500, text="Internal Error")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        transport=transport, base_url="https://gitlab.com/api/v4"
    ) as client:
        adapter = GitLabAdapter(token="token", client=client)

        with pytest.raises(ScmAuthenticationError):
            await adapter.get_repository("err", "401")

        with pytest.raises(ScmRateLimitError):
            await adapter.get_repository("err", "429")

        with pytest.raises(ScmNotFoundError):
            await adapter.get_repository("err", "404")

        with pytest.raises(ScmError):
            await adapter.get_repository("err", "500")


# ---------------------------------------------------------------------------
# Webhook Verification & Normalization Tests
# ---------------------------------------------------------------------------


def test_verify_github_signature() -> None:
    secret = "my-webhook-secret"
    body = b'{"ref": "refs/heads/main"}'

    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    valid_header = f"sha256={signature}"

    assert verify_github_signature(body, valid_header, secret) is True
    assert verify_github_signature(body, "sha256=invalid-signature", secret) is False
    assert verify_github_signature(body, valid_header, "wrong-secret") is False
    assert verify_github_signature(body, None, secret) is False
    assert verify_github_signature(body, "badprefix", secret) is False
    assert verify_github_signature(body, valid_header, "") is False


def test_verify_gitlab_token() -> None:
    secret = "gl-secret-token"

    assert verify_gitlab_token("gl-secret-token", secret) is True
    assert verify_gitlab_token("wrong-token", secret) is False
    assert verify_gitlab_token(None, secret) is False
    assert verify_gitlab_token("gl-secret-token", "") is False


def test_normalize_github_webhook() -> None:
    push_payload = {
        "repository": {"full_name": "roytechworkforce/asdo"},
        "ref": "refs/heads/main",
        "before": "0" * 40,
        "after": "3" * 40,
        "sender": {"login": "octocat"},
    }

    event = normalize_github_webhook("push", "evt-1", push_payload)
    assert event.provider == ScmProvider.GITHUB
    assert event.event_type == WebhookEventType.PUSH
    assert event.repository_full_name == "roytechworkforce/asdo"
    assert event.before_sha is None
    assert event.after_sha == "3" * 40
    assert event.sender == "octocat"

    pr_payload = {
        "repository": {"full_name": "roytechworkforce/asdo"},
        "number": 42,
        "action": "opened",
        "pull_request": {
            "head": {"ref": "feature/branch", "sha": "4" * 40},
        },
        "sender": {"login": "contributor"},
    }

    pr_event = normalize_github_webhook("pull_request", "evt-2", pr_payload)
    assert pr_event.event_type == WebhookEventType.PULL_REQUEST
    assert pr_event.pr_number == 42
    assert pr_event.after_sha == "4" * 40
    assert pr_event.action == "opened"

    ping_event = normalize_github_webhook(
        "ping", "evt-3", {"repository": {"full_name": "org/repo"}, "sender": {"login": "admin"}}
    )
    assert ping_event.event_type == WebhookEventType.PING


def test_normalize_gitlab_webhook() -> None:
    push_payload = {
        "object_kind": "push",
        "project": {"path_with_namespace": "roytechworkforce/asdo"},
        "ref": "refs/heads/main",
        "before": "1" * 40,
        "after": "2" * 40,
        "user_username": "gitlab-user",
    }

    event = normalize_gitlab_webhook("Push Hook", "evt-4", push_payload)
    assert event.provider == ScmProvider.GITLAB
    assert event.event_type == WebhookEventType.PUSH
    assert event.before_sha == "1" * 40
    assert event.after_sha == "2" * 40

    mr_payload = {
        "object_kind": "merge_request",
        "project": {"path_with_namespace": "roytechworkforce/asdo"},
        "object_attributes": {
            "iid": 10,
            "source_branch": "patch-1",
            "action": "open",
            "last_commit": {"id": "5" * 40},
        },
        "user_username": "mr-author",
    }

    mr_event = normalize_gitlab_webhook("Merge Request Hook", "evt-5", mr_payload)
    assert mr_event.event_type == WebhookEventType.PULL_REQUEST
    assert mr_event.pr_number == 10
    assert mr_event.after_sha == "5" * 40


# ---------------------------------------------------------------------------
# Factory Tests
# ---------------------------------------------------------------------------


def test_scm_factory() -> None:
    gh_adapter = get_scm_adapter("github", token="gh-token")
    assert isinstance(gh_adapter, GitHubAdapter)
    assert gh_adapter.provider == ScmProvider.GITHUB

    gl_adapter = get_scm_adapter(ScmProvider.GITLAB, token="gl-token")
    assert isinstance(gl_adapter, GitLabAdapter)
    assert gl_adapter.provider == ScmProvider.GITLAB

    with pytest.raises(ScmError):
        get_scm_adapter("bitbucket")
