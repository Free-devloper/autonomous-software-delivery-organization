from pathlib import Path
from uuid import UUID

from autonomous_sdo_api.patch.engine import PatchEngine
from autonomous_sdo_api.patch.models import PatchProposal
from autonomous_sdo_api.planning.models import WorkPackage


class CodingAgent:
    """Specialist agent that generates content-addressed code patches for work packages."""

    def __init__(self, engine: PatchEngine | None = None) -> None:
        self.engine = engine or PatchEngine()

    async def generate_code_patch(
        self,
        organization_id: UUID,
        work_package: WorkPackage,
        requirement_title: str,
        worktree_root: Path,
        proposed_file_modifications: dict[str, str],
    ) -> PatchProposal:
        """Create a patch proposal representing the changes required for the work package."""
        original_files: dict[str, str] = {}

        for relative_path in proposed_file_modifications:
            file_path = worktree_root / relative_path
            if file_path.exists() and file_path.is_file():
                original_files[relative_path] = file_path.read_text(
                    encoding="utf-8", errors="replace"
                )

        summary = f"Implement work package {work_package.id} for requirement: {requirement_title}"

        return self.engine.create_proposal_from_diff(
            organization_id=organization_id,
            work_package_id=work_package.id,
            summary=summary,
            original_files=original_files,
            modified_files=proposed_file_modifications,
        )
