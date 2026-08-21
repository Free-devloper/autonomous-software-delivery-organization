import difflib
import hashlib
from pathlib import Path
from uuid import UUID

from autonomous_sdo_api.patch.models import (
    FilePatch,
    MergeConflict,
    PatchApplicationResult,
    PatchHunk,
    PatchOperation,
    PatchProposal,
    compute_patch_digest,
)
from autonomous_sdo_api.sandbox.fs_guard import SandboxFSGuard


class PatchEngine:
    """Deterministic content-addressed unified diff engine with 3-way conflict detection."""

    @staticmethod
    def create_proposal_from_diff(
        organization_id: UUID,
        work_package_id: str,
        summary: str,
        original_files: dict[str, str],
        modified_files: dict[str, str],
    ) -> PatchProposal:
        """Generate a content-addressed PatchProposal from before/after file maps."""
        all_paths = sorted(set(original_files.keys()) | set(modified_files.keys()))
        file_patches: list[FilePatch] = []

        for path in all_paths:
            orig = original_files.get(path)
            mod = modified_files.get(path)

            if orig is None and mod is not None:
                # Added file
                lines = mod.splitlines(keepends=True)
                hunk = PatchHunk(
                    old_start=0,
                    old_lines=0,
                    new_start=1,
                    new_lines=len(lines),
                    lines=[f"+{line.rstrip('\r\n')}" for line in lines],
                )
                file_patches.append(
                    FilePatch(
                        path=path,
                        operation=PatchOperation.ADD,
                        hunks=[hunk] if lines else [],
                        new_sha=hashlib.sha1(mod.encode("utf-8")).hexdigest(),
                    )
                )
            elif orig is not None and mod is None:
                # Deleted file
                lines = orig.splitlines(keepends=True)
                hunk = PatchHunk(
                    old_start=1,
                    old_lines=len(lines),
                    new_start=0,
                    new_lines=0,
                    lines=[f"-{line.rstrip('\r\n')}" for line in lines],
                )
                file_patches.append(
                    FilePatch(
                        path=path,
                        operation=PatchOperation.DELETE,
                        hunks=[hunk] if lines else [],
                        old_sha=hashlib.sha1(orig.encode("utf-8")).hexdigest(),
                    )
                )
            elif orig is not None and mod is not None and orig != mod:
                # Modified file
                orig_lines = orig.splitlines(keepends=True)
                mod_lines = mod.splitlines(keepends=True)
                diff = list(
                    difflib.unified_diff(
                        orig_lines,
                        mod_lines,
                        fromfile=f"a/{path}",
                        tofile=f"b/{path}",
                        n=3,
                    )
                )
                hunks: list[PatchHunk] = []
                current_lines: list[str] = []
                old_start, old_len, new_start, new_len = 0, 0, 0, 0

                for line in diff:
                    if line.startswith("@@"):
                        if current_lines:
                            hunks.append(
                                PatchHunk(
                                    old_start=old_start,
                                    old_lines=old_len,
                                    new_start=new_start,
                                    new_lines=new_len,
                                    lines=current_lines,
                                )
                            )
                            current_lines = []
                        # Parse hunk header @@ -old_start,old_len +new_start,new_len @@
                        parts = line.strip().split(" ")
                        if len(parts) >= 3:
                            old_part = parts[1].lstrip("-").split(",")
                            new_part = parts[2].lstrip("+").split(",")
                            old_start = int(old_part[0])
                            old_len = int(old_part[1]) if len(old_part) > 1 else 1
                            new_start = int(new_part[0])
                            new_len = int(new_part[1]) if len(new_part) > 1 else 1
                    elif not line.startswith("---") and not line.startswith("+++"):
                        current_lines.append(line.rstrip("\r\n"))

                if current_lines:
                    hunks.append(
                        PatchHunk(
                            old_start=old_start,
                            old_lines=old_len,
                            new_start=new_start,
                            new_lines=new_len,
                            lines=current_lines,
                        )
                    )

                file_patches.append(
                    FilePatch(
                        path=path,
                        operation=PatchOperation.MODIFY,
                        hunks=hunks,
                        old_sha=hashlib.sha1(orig.encode("utf-8")).hexdigest(),
                        new_sha=hashlib.sha1(mod.encode("utf-8")).hexdigest(),
                    )
                )

        digest = compute_patch_digest(work_package_id, file_patches)

        return PatchProposal(
            organization_id=organization_id,
            work_package_id=work_package_id,
            summary=summary,
            digest_sha256=digest,
            files=file_patches,
        )

    @staticmethod
    def detect_conflicts(worktree: Path, proposal: PatchProposal) -> list[MergeConflict]:
        """Detect file collisions or content divergence before applying proposal."""
        conflicts: list[MergeConflict] = []

        for fpatch in proposal.files:
            target_path = SandboxFSGuard.validate_path(worktree, fpatch.path)

            if fpatch.operation == PatchOperation.ADD:
                if target_path.exists():
                    conflicts.append(
                        MergeConflict(
                            path=fpatch.path,
                            reason="File already exists in worktree.",
                            actual_content=target_path.read_text(
                                encoding="utf-8", errors="replace"
                            ),
                        )
                    )
            elif fpatch.operation in (PatchOperation.MODIFY, PatchOperation.DELETE):
                if not target_path.exists():
                    conflicts.append(
                        MergeConflict(
                            path=fpatch.path,
                            reason="Target file does not exist in worktree.",
                        )
                    )
                elif fpatch.old_sha:
                    actual_content = target_path.read_text(encoding="utf-8", errors="replace")
                    actual_sha = hashlib.sha1(actual_content.encode("utf-8")).hexdigest()
                    if actual_sha != fpatch.old_sha:
                        conflicts.append(
                            MergeConflict(
                                path=fpatch.path,
                                reason=f"SHA mismatch ({fpatch.old_sha} != {actual_sha}).",
                                actual_content=actual_content,
                            )
                        )

        return conflicts

    @staticmethod
    def apply_proposal(
        worktree: Path,
        proposal: PatchProposal,
        modified_contents: dict[str, str] | None = None,
    ) -> PatchApplicationResult:
        """Apply patch proposal with validation and deterministic conflict detection."""
        conflicts = PatchEngine.detect_conflicts(worktree, proposal)
        if conflicts:
            return PatchApplicationResult(
                proposal_id=proposal.id,
                applied=False,
                conflicts=conflicts,
            )

        content_map = modified_contents or {}

        for fpatch in proposal.files:
            target_path = SandboxFSGuard.validate_path(worktree, fpatch.path)

            if fpatch.operation == PatchOperation.DELETE:
                if target_path.exists():
                    target_path.unlink()
            elif fpatch.operation == PatchOperation.ADD:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                new_text = content_map.get(fpatch.path, "")
                if not new_text and fpatch.hunks:
                    new_text = "\n".join(
                        line[1:] for h in fpatch.hunks for line in h.lines if line.startswith("+")
                    )
                target_path.write_text(new_text, encoding="utf-8")
            elif fpatch.operation == PatchOperation.MODIFY:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                if fpatch.path in content_map:
                    target_path.write_text(content_map[fpatch.path], encoding="utf-8")
                elif fpatch.hunks:
                    new_text = "\n".join(
                        line[1:]
                        for h in fpatch.hunks
                        for line in h.lines
                        if not line.startswith("-")
                    )
                    target_path.write_text(new_text, encoding="utf-8")

        # Compute synthetic commit SHA
        committed_sha = hashlib.sha1(f"{proposal.id}:{proposal.digest_sha256}".encode()).hexdigest()

        return PatchApplicationResult(
            proposal_id=proposal.id,
            applied=True,
            conflicts=[],
            committed_sha=committed_sha,
        )
