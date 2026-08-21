from pathlib import Path

from autonomous_sdo_api.repository.models import (
    FileContentResponse,
    FileEntry,
    FileEntryType,
    LexicalSearchMatch,
    RepositoryError,
)
from autonomous_sdo_api.repository.path_guard import sanitize_and_contain_path

EXCLUDED_DIRECTORIES = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        ".next",
        "dist",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        ".turbo",
        ".gemini",
    }
)


class RepositoryExplorerService:
    """Service to browse file trees, inspect source code blobs, and search repository files."""

    def __init__(self, default_max_file_size: int = 2_000_000) -> None:
        self.default_max_file_size = default_max_file_size

    def get_file_tree(self, base_path: Path, subpath: str = "") -> list[FileEntry]:
        """List file and directory entries for a contained subpath."""
        resolved_base = base_path.resolve()
        target_dir = sanitize_and_contain_path(resolved_base, subpath)

        if not target_dir.exists():
            raise RepositoryError(f"Directory not found: '{subpath}'")
        if not target_dir.is_dir():
            raise RepositoryError(f"Path is not a directory: '{subpath}'")

        entries: list[FileEntry] = []
        for item in sorted(target_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            if item.name in EXCLUDED_DIRECTORIES:
                continue

            try:
                rel_path = item.resolve().relative_to(resolved_base).as_posix()
            except ValueError:
                rel_path = item.name

            if item.is_symlink():
                entry_type = FileEntryType.SYMLINK
                size = 0
            elif item.is_dir():
                entry_type = FileEntryType.DIRECTORY
                size = 0
            else:
                entry_type = FileEntryType.FILE
                size = item.stat().st_size

            entries.append(
                FileEntry(
                    name=item.name,
                    path=rel_path,
                    type=entry_type,
                    size_bytes=size,
                )
            )

        return entries

    def get_file_blob(
        self,
        base_path: Path,
        file_path: str,
        commit_sha: str,
        max_bytes: int | None = None,
    ) -> FileContentResponse:
        """Read and inspect the content of a file within the repository."""
        resolved_base = base_path.resolve()
        target_file = sanitize_and_contain_path(resolved_base, file_path)

        if not target_file.exists():
            raise RepositoryError(f"File not found: '{file_path}'")
        if not target_file.is_file():
            raise RepositoryError(f"Path is not a file: '{file_path}'")

        limit = max_bytes or self.default_max_file_size
        raw_bytes = target_file.read_bytes()
        size_bytes = len(raw_bytes)

        # Truncate if exceeds limit
        truncated_bytes = raw_bytes[:limit]

        # Check for binary content (null byte detection in sample)
        sample = truncated_bytes[:8192]
        is_binary = b"\x00" in sample

        if is_binary:
            content = f"<binary data: {size_bytes} bytes>"
            lines_count = 0
        else:
            try:
                content = truncated_bytes.decode("utf-8")
            except UnicodeDecodeError:
                content = truncated_bytes.decode("latin-1", errors="replace")
            lines_count = content.count("\n") + (1 if content else 0)

        try:
            rel_path = target_file.resolve().relative_to(resolved_base).as_posix()
        except ValueError:
            rel_path = target_file.name

        return FileContentResponse(
            commit_sha=commit_sha,
            path=rel_path,
            content=content,
            is_binary=is_binary,
            size_bytes=size_bytes,
            lines_count=lines_count,
        )

    def search_lexical(
        self,
        base_path: Path,
        query: str,
        max_matches: int = 100,
    ) -> list[LexicalSearchMatch]:
        """Perform case-insensitive lexical search across text files within base_path."""
        if not query.strip():
            return []

        resolved_base = base_path.resolve()
        matches: list[LexicalSearchMatch] = []
        lower_query = query.lower()

        for item in sorted(resolved_base.rglob("*")):
            if len(matches) >= max_matches:
                break
            if not item.is_file() or any(part in EXCLUDED_DIRECTORIES for part in item.parts):
                continue

            try:
                rel_path = item.resolve().relative_to(resolved_base).as_posix()
            except ValueError:
                continue

            try:
                raw_bytes = item.read_bytes()
                if b"\x00" in raw_bytes[:4096]:  # Skip binary files
                    continue
                text = raw_bytes.decode("utf-8", errors="ignore")
            except (OSError, UnicodeDecodeError):
                continue

            for line_idx, line in enumerate(text.splitlines(), start=1):
                if lower_query in line.lower():
                    matches.append(
                        LexicalSearchMatch(
                            path=rel_path,
                            line_number=line_idx,
                            line_content=line.strip()[:200],
                        )
                    )
                    if len(matches) >= max_matches:
                        break

        return matches
