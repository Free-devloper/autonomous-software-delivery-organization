import subprocess
import tempfile
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from autonomous_sdo_api.app import create_app
from autonomous_sdo_api.config import Settings
from autonomous_sdo_api.database.tenancy import OrganizationContext, get_organization_context
from autonomous_sdo_api.policy import Role
from autonomous_sdo_api.repository import (
    FileEntryType,
    PathTraversalError,
    RepositoryError,
    RepositoryExplorerService,
    WorktreeError,
    WorktreeManager,
    sanitize_and_contain_path,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Path Guard Tests
# ---------------------------------------------------------------------------


def test_path_guard_valid() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        sub = base / "src" / "pkg"
        sub.mkdir(parents=True)
        file = sub / "mod.py"
        file.write_text("print('test')")

        resolved = sanitize_and_contain_path(base, "src/pkg/mod.py")
        assert resolved == file.resolve()

        resolved_dir = sanitize_and_contain_path(base, "src/pkg")
        assert resolved_dir == sub.resolve()

        resolved_root = sanitize_and_contain_path(base, "")
        assert resolved_root == base.resolve()


def test_path_guard_traversal_attempts() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)

        with pytest.raises(PathTraversalError):
            sanitize_and_contain_path(base, "../escaped.txt")

        with pytest.raises(PathTraversalError):
            sanitize_and_contain_path(base, "../../etc/passwd")

        with pytest.raises(PathTraversalError):
            sanitize_and_contain_path(base, "src/../../outside")

        with pytest.raises(PathTraversalError):
            sanitize_and_contain_path(base, "foo/bar\x00baz")


# ---------------------------------------------------------------------------
# Worktree Manager Tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_worktree_manager_lifecycle() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root_storage = Path(tmp_dir)
        manager = WorktreeManager(root_storage)

        mirror = root_storage / "fake_repo"
        mirror.mkdir()

        sha = "a" * 40
        async with await manager.create_worktree(mirror, sha, worktree_id="test1234") as wt:
            assert wt.commit_sha == sha
            assert wt.worktree_path.exists()
            assert "wt_aaaaaaaaaa_test1234" in wt.worktree_path.name

        # Verify auto-cleanup after context exit
        assert not wt.worktree_path.exists()


@pytest.mark.anyio
async def test_worktree_manager_git_repo() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root_storage = Path(tmp_dir)
        repo_dir = root_storage / "sample_git_repo"
        repo_dir.mkdir()

        # Initialize a real git repo
        subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@asdo.org"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "ASDO Test"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
        test_file = repo_dir / "README.md"
        test_file.write_text("# Hello ASDO")
        subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "init commit"], cwd=repo_dir, check=True, capture_output=True
        )

        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo_dir, check=True, capture_output=True, text=True
        )
        sha = proc.stdout.strip()

        manager = WorktreeManager(root_storage)
        async with await manager.create_worktree(repo_dir, sha, worktree_id="wtgit") as wt:
            assert wt.worktree_path.exists()
            assert (wt.worktree_path / "README.md").exists()

        assert not wt.worktree_path.exists()

        # Test failure on invalid commit sha
        with pytest.raises(WorktreeError):
            await manager.create_worktree(repo_dir, "0" * 40, worktree_id="wtinvalid")


# ---------------------------------------------------------------------------
# Repository Explorer Service Tests
# ---------------------------------------------------------------------------


def test_repository_explorer_tree_and_blobs() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        git_dir = base / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("git config")

        src = base / "src"
        src.mkdir()
        main_file = src / "main.py"
        main_file.write_text("print('hello world')\nprint('second line')")

        bin_file = base / "image.png"
        bin_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")

        service = RepositoryExplorerService()

        # Tree listing
        root_entries = service.get_file_tree(base)
        names = [e.name for e in root_entries]
        assert ".git" not in names
        assert "src" in names
        assert "image.png" in names
        assert root_entries[0].type == FileEntryType.DIRECTORY

        src_entries = service.get_file_tree(base, "src")
        assert len(src_entries) == 1
        assert src_entries[0].name == "main.py"
        assert src_entries[0].type == FileEntryType.FILE

        with pytest.raises(RepositoryError):
            service.get_file_tree(base, "non_existent")

        # Blob inspection
        sha = "b" * 40
        blob = service.get_file_blob(base, "src/main.py", sha)
        assert blob.is_binary is False
        assert blob.lines_count == 2
        assert "hello world" in blob.content

        # Truncation test
        truncated = service.get_file_blob(base, "src/main.py", sha, max_bytes=10)
        assert len(truncated.content) == 10

        bin_blob = service.get_file_blob(base, "image.png", sha)
        assert bin_blob.is_binary is True
        assert "<binary data" in bin_blob.content

        with pytest.raises(RepositoryError):
            service.get_file_blob(base, "missing.txt", sha)


def test_repository_explorer_lexical_search() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        f1 = base / "file1.txt"
        f1.write_text("The quick brown fox\njumps over the lazy dog")
        f2 = base / "file2.py"
        f2.write_text("def find_fox():\n    return 'FOX'")

        service = RepositoryExplorerService()

        matches = service.search_lexical(base, "fox")
        assert len(matches) == 3
        assert any(m.path == "file1.txt" and m.line_number == 1 for m in matches)
        assert any(m.path == "file2.py" for m in matches)

        assert service.search_lexical(base, "") == []
        assert service.search_lexical(base, "nonexistent_query") == []


# ---------------------------------------------------------------------------
# Repository API Routes Tests
# ---------------------------------------------------------------------------


def test_repository_routes() -> None:
    settings = Settings(service_name="asdo-test-repo")
    app = create_app(settings=settings)
    client = TestClient(app)

    # Health live
    res_health = client.get("/api/v1/health/live")
    assert res_health.status_code == 200

    sha = "c" * 40
    # Routes fail closed (503 unconfigured auth or 401 unauthenticated)
    res_tree_unauth = client.get(f"/api/v1/repositories/tree?commit_sha={sha}")
    assert res_tree_unauth.status_code in (401, 503)

    # Override organization context to test authenticated calls
    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        organization_id=UUID("018f0000-0000-7000-8000-000000000001"),
        actor_id="usr-test-1",
        roles=frozenset({Role.REPOSITORY_MAINTAINER}),
    )

    res_tree = client.get(f"/api/v1/repositories/tree?commit_sha={sha}")
    assert res_tree.status_code == 200
    tree_data = res_tree.json()
    assert tree_data["commit_sha"] == sha
    assert len(tree_data["entries"]) > 0

    res_blob = client.get(
        f"/api/v1/repositories/blob?commit_sha={sha}&file_path=services/api/pyproject.toml"
    )
    assert res_blob.status_code == 200
    blob_data = res_blob.json()
    assert blob_data["commit_sha"] == sha
    assert blob_data["is_binary"] is False

    res_search = client.get(f"/api/v1/repositories/search?commit_sha={sha}&query=autonomous")
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert search_data["total_matches"] > 0


def test_repository_routes_error_handling() -> None:
    settings = Settings(service_name="asdo-test-repo")
    app = create_app(settings=settings)
    client = TestClient(app)
    sha = "d" * 40

    # Test 403 Forbidden with unauthorized role
    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        organization_id=UUID("018f0000-0000-7000-8000-000000000001"),
        actor_id="usr-test-1",
        roles=frozenset({Role.BILLING_ADMINISTRATOR}),
    )
    res_forbidden = client.get(f"/api/v1/repositories/tree?commit_sha={sha}")
    assert res_forbidden.status_code == 403

    # Switch to authorized role
    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        organization_id=UUID("018f0000-0000-7000-8000-000000000001"),
        actor_id="usr-test-1",
        roles=frozenset({Role.ORGANIZATION_ADMINISTRATOR}),
    )

    # 400 on traversal attempt
    res_traversal_tree = client.get(
        f"/api/v1/repositories/tree?commit_sha={sha}&subpath=../escaped"
    )
    assert res_traversal_tree.status_code == 400

    res_traversal_blob = client.get(
        f"/api/v1/repositories/blob?commit_sha={sha}&file_path=../../etc/passwd"
    )
    assert res_traversal_blob.status_code == 400

    # 404 on not found
    res_not_found_tree = client.get(
        f"/api/v1/repositories/tree?commit_sha={sha}&subpath=non_existent_dir_123"
    )
    assert res_not_found_tree.status_code == 404

    res_not_found_blob = client.get(
        f"/api/v1/repositories/blob?commit_sha={sha}&file_path=non_existent_file_123.txt"
    )
    assert res_not_found_blob.status_code == 404
