from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import pytest

from autonomous_sdo_api.sandbox.fs_guard import SandboxFSGuard
from autonomous_sdo_api.sandbox.models import (
    ExecutionCommand,
    ForbiddenMountViolation,
    NetworkPolicy,
    PathTraversalViolation,
    SandboxDescriptor,
    SandboxLimits,
    SandboxProfile,
    SymlinkBreakoutViolation,
)
from autonomous_sdo_api.sandbox.network_guard import SandboxNetworkGuard
from autonomous_sdo_api.sandbox.rootless import RootlessContainerAdapter
from autonomous_sdo_api.sandbox.secrets import REDACTED_PLACEHOLDER, SecretScrubber

pytestmark = pytest.mark.unit


def test_path_traversal_prevention() -> None:
    with TemporaryDirectory() as tmpdir:
        worktree = Path(tmpdir) / "worktree"
        worktree.mkdir()

        # Valid subpaths within sandbox
        valid_p = SandboxFSGuard.validate_path(worktree, "src/index.ts")
        assert valid_p == (worktree / "src/index.ts").resolve()

        # Path traversal with ../
        with pytest.raises(PathTraversalViolation):
            SandboxFSGuard.validate_path(worktree, "../../etc/passwd")

        with pytest.raises(PathTraversalViolation):
            SandboxFSGuard.validate_path(worktree, "foo/../../outside")

        # Null byte injection
        with pytest.raises(PathTraversalViolation):
            SandboxFSGuard.validate_path(worktree, "safe/path\x00/../../etc/passwd")


def test_symlink_breakout_prevention() -> None:
    with TemporaryDirectory() as tmpdir:
        worktree = Path(tmpdir) / "worktree"
        worktree.mkdir()

        # Valid relative symlink within sandbox
        valid_sym = SandboxFSGuard.validate_symlink(worktree, "internal/target.py")
        assert valid_sym == (worktree / "internal/target.py").resolve()

        # Symlink target escaping sandbox
        with pytest.raises(SymlinkBreakoutViolation):
            SandboxFSGuard.validate_symlink(worktree, "../../root/secret.key")

        with pytest.raises(SymlinkBreakoutViolation):
            SandboxFSGuard.validate_symlink(worktree, "/etc/shadow")


def test_forbidden_mount_prevention() -> None:
    # Prohibit mounting Docker socket
    with pytest.raises(ForbiddenMountViolation):
        SandboxFSGuard.assert_mount_safe("/var/run/docker.sock")

    with pytest.raises(ForbiddenMountViolation):
        SandboxFSGuard.assert_mount_safe("//./pipe/docker_engine")

    with pytest.raises(ForbiddenMountViolation):
        SandboxFSGuard.assert_mount_safe("containerd.sock")

    # Prohibit mounting host root
    with pytest.raises(ForbiddenMountViolation):
        SandboxFSGuard.assert_mount_safe("/")


def test_secret_scrubber_redacts_tokens() -> None:
    # 1. Explicit canary secret
    canary = "SUPER_SECRET_CANARY_VALUE_999"
    raw_text = f"DEBUG: Process started with key={canary} and completed successfully."
    scrubbed, count = SecretScrubber.scrub(raw_text, [canary])
    assert canary not in scrubbed
    assert REDACTED_PLACEHOLDER in scrubbed
    assert count == 1

    # 2. GitHub PAT pattern
    gh_pat = "".join(["gh", "p_", "mocktokenforsecretscrubber1234567890"])
    raw_pat_text = f"Cloning git repo using {gh_pat} authorization."
    scrubbed_pat, count_pat = SecretScrubber.scrub(raw_pat_text)
    assert gh_pat not in scrubbed_pat
    assert REDACTED_PLACEHOLDER in scrubbed_pat
    assert count_pat == 1

    # 3. Multiple secrets
    mixed_text = f"auth token: {canary}, git token: {gh_pat}"
    scrubbed_mixed, count_mixed = SecretScrubber.scrub(mixed_text, [canary])
    assert canary not in scrubbed_mixed
    assert gh_pat not in scrubbed_mixed
    assert count_mixed == 2


def test_network_isolation_policy_env() -> None:
    # Deny all policy
    deny_env = SandboxNetworkGuard.get_network_isolation_env(NetworkPolicy.DENY_ALL)
    assert deny_env["NO_PROXY"] == "*"
    assert deny_env["HTTP_PROXY"] == "http://127.0.0.1:0"
    assert deny_env["ASDO_NETWORK_ISOLATION"] == "deny_all"

    # Allow internal policy
    internal_env = SandboxNetworkGuard.get_network_isolation_env(
        NetworkPolicy.ALLOW_INTERNAL_ONLY, ["auth.internal", "db.internal"]
    )
    assert internal_env["NO_PROXY"] == "auth.internal,db.internal"
    assert internal_env["ASDO_NETWORK_ISOLATION"] == "allow_internal_only"


@pytest.mark.anyio
async def test_ephemeral_secrets_in_rootless_execution() -> None:
    with TemporaryDirectory() as tmpdir:
        adapter = RootlessContainerAdapter(base_sandbox_dir=Path(tmpdir))
        canary_secret = "CANARY_INJECTED_SECRET_XYZ987"
        descriptor = SandboxDescriptor(
            organization_id=uuid4(),
            requirement_id="req-sec",
            plan_id="plan-sec",
            work_package_id="pkg-sec",
            profile=SandboxProfile.ROOTLESS_CONTAINER,
            limits=SandboxLimits(network_policy=NetworkPolicy.DENY_ALL),
            worktree_path=str(Path(tmpdir) / "worktree-sec"),
        )
        await adapter.provision(descriptor)

        cmd = ExecutionCommand(
            command="python",
            args=[
                "-c",
                "import os; print(f'Revealed key: {os.environ.get(\"SECRET_CANARY\")}')",
            ],
            ephemeral_secrets={"SECRET_CANARY": canary_secret},
        )
        res = await adapter.execute(descriptor, cmd)
        assert res.exit_code == 0
        # Secret value must NEVER appear in output
        assert canary_secret not in res.stdout
        assert canary_secret not in res.stderr
        assert REDACTED_PLACEHOLDER in res.stdout
        assert res.redacted_secrets_count >= 1

        await adapter.terminate(descriptor)
