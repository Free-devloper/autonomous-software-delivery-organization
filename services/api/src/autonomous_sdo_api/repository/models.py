from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

COMMIT_SHA_REGEX = r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$"
CommitSha = Annotated[str, StringConstraints(pattern=COMMIT_SHA_REGEX)]


class FileEntryType(StrEnum):
    FILE = "file"
    DIRECTORY = "directory"
    SYMLINK = "symlink"


class RepositoryError(Exception):
    """Base exception for repository operations."""


class PathTraversalError(RepositoryError):
    """Raised when an access attempt breaches the repository directory boundary."""


class WorktreeError(RepositoryError):
    """Raised when worktree lifecycle operations fail."""


class FileEntry(BaseModel):
    """Metadata representing a single item in a repository directory."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    path: str
    type: FileEntryType
    size_bytes: int = Field(ge=0)


class FileTreeResponse(BaseModel):
    """Directory tree listing response at a specific commit."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    commit_sha: CommitSha
    path: str = ""
    entries: list[FileEntry] = Field(default_factory=list)


class FileContentResponse(BaseModel):
    """File content blob at a specific commit."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    commit_sha: CommitSha
    path: str = Field(min_length=1)
    content: str
    is_binary: bool = False
    size_bytes: int = Field(ge=0)
    lines_count: int = Field(ge=0)


class LexicalSearchMatch(BaseModel):
    """Single matching line in lexical search."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    line_number: int = Field(gt=0)
    line_content: str


class LexicalSearchResult(BaseModel):
    """Result of lexical search across repository files."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    commit_sha: CommitSha
    query: str = Field(min_length=1)
    total_matches: int = Field(ge=0)
    matches: list[LexicalSearchMatch] = Field(default_factory=list)
