import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class PatchOperation(StrEnum):
    ADD = "add"
    MODIFY = "modify"
    DELETE = "delete"
    RENAME = "rename"


class PatchHunk(BaseModel):
    old_start: int = Field(ge=0)
    old_lines: int = Field(ge=0)
    new_start: int = Field(ge=0)
    new_lines: int = Field(ge=0)
    lines: list[str] = Field(default_factory=list)


class FilePatch(BaseModel):
    path: str = Field(min_length=1)
    operation: PatchOperation
    old_path: str | None = None
    hunks: list[PatchHunk] = Field(default_factory=list)
    old_sha: str | None = None
    new_sha: str | None = None


def compute_patch_digest(work_package_id: str, files: list[FilePatch]) -> str:
    """Compute deterministic SHA-256 digest from canonical JSON representation of file patches."""
    payload = {
        "work_package_id": work_package_id,
        "files": [
            {
                "path": f.path,
                "operation": f.operation.value,
                "old_path": f.old_path,
                "hunks": [
                    {
                        "old_start": h.old_start,
                        "old_lines": h.old_lines,
                        "new_start": h.new_start,
                        "new_lines": h.new_lines,
                        "lines": h.lines,
                    }
                    for h in f.hunks
                ],
            }
            for f in sorted(files, key=lambda x: x.path)
        ],
    }
    canonical_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()


class PatchProposal(BaseModel):
    id: str = Field(default_factory=lambda: f"patch_{uuid4().hex[:12]}")
    organization_id: UUID
    work_package_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    digest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    files: list[FilePatch] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MergeConflict(BaseModel):
    path: str
    reason: str
    expected_content: str | None = None
    actual_content: str | None = None


class PatchApplicationResult(BaseModel):
    proposal_id: str
    applied: bool
    conflicts: list[MergeConflict] = Field(default_factory=list)
    committed_sha: str | None = None


class CreatePatchProposalRequest(BaseModel):
    work_package_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    files: list[FilePatch] = Field(min_length=1)


class PatchNotFoundError(KeyError):
    pass
