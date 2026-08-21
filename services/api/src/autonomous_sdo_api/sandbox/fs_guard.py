from pathlib import Path

from autonomous_sdo_api.sandbox.models import (
    ForbiddenMountViolation,
    PathTraversalViolation,
    SymlinkBreakoutViolation,
)

_FORBIDDEN_SOCKET_PATTERNS = (
    "docker.sock",
    "dockershim.sock",
    "containerd.sock",
    "crio.sock",
    "podman.sock",
    "/var/run/docker",
    "//./pipe/docker",
)

_FORBIDDEN_HOST_ROOTS = (
    Path("/"),
    Path("/etc"),
    Path("/root"),
    Path("/sys"),
    Path("/proc"),
    Path("/dev"),
    Path("C:\\"),
    Path("C:\\Windows"),
)


class SandboxFSGuard:
    """Hardened filesystem path containment and mount boundary validation."""

    @staticmethod
    def validate_path(worktree_root: Path, subpath: str | Path | None) -> Path:
        """Resolve subpath and ensure it remains strictly contained inside the worktree root."""
        root = worktree_root.resolve()
        if subpath is None or str(subpath).strip() in ("", "."):
            return root

        subpath_str = str(subpath)
        if "\x00" in subpath_str:
            raise PathTraversalViolation("Null byte injection detected in sandbox path.")

        # Check for path traversal components
        clean_subpath = Path(subpath_str)
        if clean_subpath.is_absolute():
            resolved = clean_subpath.resolve()
        else:
            resolved = (root / clean_subpath).resolve()

        try:
            resolved.relative_to(root)
        except ValueError as err:
            raise PathTraversalViolation(
                f"Path '{subpath_str}' escapes sandbox worktree '{root}'"
            ) from err

        return resolved

    @staticmethod
    def validate_symlink(worktree_root: Path, target_path: str | Path) -> Path:
        """Verify that a symlink target resolves to a path inside the sandbox worktree."""
        root = worktree_root.resolve()
        target_str = str(target_path)
        if "\x00" in target_str:
            raise SymlinkBreakoutViolation("Null byte injection in symlink target.")

        target = Path(target_str)
        resolved_target = target.resolve() if target.is_absolute() else (root / target).resolve()

        try:
            resolved_target.relative_to(root)
        except ValueError as err:
            raise SymlinkBreakoutViolation(
                f"Symlink target '{target_str}' escapes sandbox boundary."
            ) from err

        return resolved_target

    @staticmethod
    def assert_mount_safe(mount_source: str | Path) -> None:
        """Ensure mount source does not target host Docker sockets or prohibited root fs."""
        source_str = str(mount_source).lower()
        for forbidden in _FORBIDDEN_SOCKET_PATTERNS:
            if forbidden.lower() in source_str:
                raise ForbiddenMountViolation(
                    f"Mounting host container runtime socket '{mount_source}' is prohibited."
                )

        resolved_mount = Path(mount_source).resolve()
        for forbidden_root in _FORBIDDEN_HOST_ROOTS:
            if resolved_mount == forbidden_root.resolve():
                raise ForbiddenMountViolation(
                    f"Direct mounting of host root directory '{mount_source}' is prohibited."
                )
