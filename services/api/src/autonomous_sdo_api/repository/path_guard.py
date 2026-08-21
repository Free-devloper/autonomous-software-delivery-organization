from pathlib import Path

from autonomous_sdo_api.repository.models import PathTraversalError


def sanitize_and_contain_path(base_dir: Path, relative_path: str) -> Path:
    """Validate and resolve a path to ensure it remains strictly contained within base_dir.

    Guards against:
    - Null-byte injections
    - Directory traversal sequences (../)
    - Absolute path overrides (/etc, C:\\)
    - Symlink escapes pointing outside base_dir
    """
    if "\x00" in relative_path:
        raise PathTraversalError("Null bytes are prohibited in paths")

    clean_rel = relative_path.strip().lstrip("/\\")
    if not clean_rel:
        return base_dir.resolve()

    # Construct the target path without resolving symlinks first
    target = base_dir / clean_rel

    # Resolve canonical path
    try:
        resolved_base = base_dir.resolve()
        resolved_target = target.resolve()
    except (OSError, RuntimeError) as err:
        raise PathTraversalError(f"Failed to resolve path safely: {err}") from err

    # Ensure the resolved target is contained within the resolved base directory
    try:
        resolved_target.relative_to(resolved_base)
    except ValueError as err:
        raise PathTraversalError(
            f"Path traversal detected: '{relative_path}' escapes base directory '{base_dir}'"
        ) from err

    return resolved_target
