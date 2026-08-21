from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from autonomous_sdo_api.app import create_app
from autonomous_sdo_api.config import Settings
from autonomous_sdo_api.patch.agent import CodingAgent
from autonomous_sdo_api.patch.engine import PatchEngine
from autonomous_sdo_api.patch.models import (
    FilePatch,
    PatchOperation,
    PatchProposal,
    compute_patch_digest,
)
from autonomous_sdo_api.planning.models import (
    SpecialistRole,
    WorkPackage,
    WorkPackageBudget,
    WorkPackageStatus,
)

pytestmark = pytest.mark.unit


def test_compute_patch_digest_is_deterministic() -> None:
    wp_id = "pkg-auth-1"
    files = [
        FilePatch(
            path="src/auth.py",
            operation=PatchOperation.MODIFY,
            old_sha="abc1234",
            new_sha="def5678",
        ),
        FilePatch(
            path="src/session.py",
            operation=PatchOperation.ADD,
            new_sha="11223344",
        ),
    ]

    digest_1 = compute_patch_digest(wp_id, files)
    digest_2 = compute_patch_digest(wp_id, list(reversed(files)))  # Order independent

    assert len(digest_1) == 64
    assert digest_1 == digest_2


def test_patch_engine_creation_and_apply_lifecycle() -> None:
    with TemporaryDirectory() as tmpdir:
        worktree = Path(tmpdir) / "worktree"
        worktree.mkdir()

        # Seed an original file
        main_py = worktree / "main.py"
        main_py.write_text("print('hello world')\n", encoding="utf-8")

        org_id = uuid4()
        original_files = {"main.py": "print('hello world')\n"}
        modified_files = {
            "main.py": "print('hello universe')\n",
            "utils.py": "def add(a, b):\n    return a + b\n",
        }

        proposal = PatchEngine.create_proposal_from_diff(
            organization_id=org_id,
            work_package_id="pkg-diff-1",
            summary="Update greetings and add math utility",
            original_files=original_files,
            modified_files=modified_files,
        )

        assert proposal.work_package_id == "pkg-diff-1"
        assert len(proposal.files) == 2
        assert len(proposal.digest_sha256) == 64

        # Apply proposal
        result = PatchEngine.apply_proposal(worktree, proposal, modified_contents=modified_files)
        assert result.applied is True
        assert len(result.conflicts) == 0
        assert result.committed_sha is not None

        # Verify filesystem contents
        assert (worktree / "main.py").read_text(encoding="utf-8") == "print('hello universe')\n"
        assert (worktree / "utils.py").read_text(
            encoding="utf-8"
        ) == "def add(a, b):\n    return a + b\n"


def test_patch_engine_conflict_detection() -> None:
    with TemporaryDirectory() as tmpdir:
        worktree = Path(tmpdir) / "worktree"
        worktree.mkdir()

        # Scenario 1: File already exists for ADD operation
        (worktree / "existing.py").write_text("existing content", encoding="utf-8")

        proposal = PatchProposal(
            organization_id=uuid4(),
            work_package_id="pkg-conflict",
            summary="Conflicting add",
            digest_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            files=[
                FilePatch(path="existing.py", operation=PatchOperation.ADD),
                FilePatch(
                    path="missing.py",
                    operation=PatchOperation.MODIFY,
                    old_sha="abc",
                ),
            ],
        )

        conflicts = PatchEngine.detect_conflicts(worktree, proposal)
        assert len(conflicts) == 2
        assert "File already exists" in conflicts[0].reason
        assert "Target file does not exist" in conflicts[1].reason

        # Attempt to apply proposal with conflicts
        apply_res = PatchEngine.apply_proposal(worktree, proposal)
        assert apply_res.applied is False
        assert len(apply_res.conflicts) == 2


@pytest.mark.anyio
async def test_coding_agent_generates_patch() -> None:
    with TemporaryDirectory() as tmpdir:
        worktree = Path(tmpdir)
        (worktree / "config.py").write_text("DEBUG = False\n", encoding="utf-8")

        wp = WorkPackage(
            id="wp-agent-1",
            requirement_id="req-agent-1",
            revision_id="rev-1",
            title="Enable debug mode",
            description="Set debug flag to true",
            target_files=["config.py"],
            assigned_specialist=SpecialistRole.BACKEND,
            status=WorkPackageStatus.IN_PROGRESS,
            budget=WorkPackageBudget(max_tokens=1000, max_cost_usd=0.05, max_duration_seconds=60),
            created_at=datetime.now(UTC),
        )

        agent = CodingAgent()
        proposal = await agent.generate_code_patch(
            organization_id=uuid4(),
            work_package=wp,
            requirement_title="Debug config update",
            worktree_root=worktree,
            proposed_file_modifications={"config.py": "DEBUG = True\n"},
        )

        assert proposal.work_package_id == "wp-agent-1"
        assert len(proposal.files) == 1
        assert proposal.files[0].operation.value == PatchOperation.MODIFY.value
        assert len(proposal.digest_sha256) == 64


def test_patch_api_routes() -> None:
    settings = Settings(service_name="asdo-patch-api-test")
    app = create_app(settings=settings)
    client = TestClient(app)

    org_id = uuid4()
    other_org = uuid4()

    from autonomous_sdo_api.database.tenancy import OrganizationContext, get_organization_context
    from autonomous_sdo_api.policy import Role

    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        organization_id=org_id,
        actor_id="user-1",
        roles=frozenset({Role.REPOSITORY_MAINTAINER}),
    )

    # 1. Create a patch proposal
    create_payload = {
        "work_package_id": "pkg-api-1",
        "summary": "Update readme documentation",
        "files": [
            {
                "path": "README.md",
                "operation": "add",
                "hunks": [
                    {
                        "old_start": 0,
                        "old_lines": 0,
                        "new_start": 1,
                        "new_lines": 1,
                        "lines": ["+# ASDO Project"],
                    }
                ],
            }
        ],
    }
    res = client.post("/api/v1/patches/proposals", json=create_payload)
    assert res.status_code == 201
    data = res.json()
    proposal_id = data["id"]
    assert data["work_package_id"] == "pkg-api-1"
    assert len(data["digest_sha256"]) == 64

    # 2. List proposals for org
    res_list = client.get("/api/v1/patches/proposals")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # 3. Cross-tenant isolation: switch to other org
    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        organization_id=other_org,
        actor_id="user-2",
        roles=frozenset({Role.REPOSITORY_MAINTAINER}),
    )

    res_other = client.get("/api/v1/patches/proposals")
    assert res_other.status_code == 200
    assert len(res_other.json()) == 0

    # 4. Other org cannot fetch proposal by ID
    res_get_other = client.get(f"/api/v1/patches/proposals/{proposal_id}")
    assert res_get_other.status_code == 404

    # 5. Switch back to org_id and apply proposal
    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        organization_id=org_id,
        actor_id="user-1",
        roles=frozenset({Role.REPOSITORY_MAINTAINER}),
    )
    res_apply = client.post(f"/api/v1/patches/proposals/{proposal_id}/apply")
    assert res_apply.status_code == 200
    apply_data = res_apply.json()
    assert apply_data["proposal_id"] == proposal_id
    assert apply_data["applied"] is True
