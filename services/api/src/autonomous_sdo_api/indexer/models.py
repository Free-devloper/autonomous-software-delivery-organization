from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from autonomous_sdo_api.repository.models import COMMIT_SHA_REGEX

CommitSha = Annotated[str, StringConstraints(pattern=COMMIT_SHA_REGEX)]


class SymbolKind(StrEnum):
    FUNCTION = "function"
    METHOD = "method"
    CLASS = "class"
    INTERFACE = "interface"
    VARIABLE = "variable"
    CONSTANT = "constant"
    TYPE_ALIAS = "type_alias"
    IMPORT = "import"


class SymbolLocation(BaseModel):
    """Zero-indexed/one-indexed coordinates in a source file."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    start_line: int = Field(gt=0)
    start_column: int = Field(ge=0)
    end_line: int = Field(gt=0)
    end_column: int = Field(ge=0)


class CodeSymbol(BaseModel):
    """Extracted semantic code symbol."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    qualified_name: str = Field(min_length=1)
    kind: SymbolKind
    location: SymbolLocation
    docstring: str | None = None
    is_exported: bool = False
    parent_id: str | None = None


class FileSymbolsResponse(BaseModel):
    """All symbols extracted from a file at a specific commit."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    commit_sha: CommitSha
    file_path: str = Field(min_length=1)
    language: str = Field(min_length=1)
    symbols: list[CodeSymbol] = Field(default_factory=list)


class SearchMode(StrEnum):
    LEXICAL = "lexical"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class ChunkType(StrEnum):
    CODE = "code"
    DOC = "doc"


class CodeChunk(BaseModel):
    """A semantic chunk of code or documentation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    chunk_id: str = Field(min_length=1)
    file_path: str = Field(min_length=1)
    start_line: int = Field(gt=0)
    end_line: int = Field(gt=0)
    content: str
    content_hash: str = Field(min_length=1)
    chunk_type: ChunkType


class SearchResultItem(BaseModel):
    """Individual ranked search result from hybrid or semantic retrieval."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    chunk_id: str = Field(min_length=1)
    file_path: str = Field(min_length=1)
    start_line: int = Field(gt=0)
    end_line: int = Field(gt=0)
    content: str
    chunk_type: ChunkType
    score: float = Field(ge=0.0)
    lexical_rank: int | None = None
    semantic_rank: int | None = None


class HybridSearchRequest(BaseModel):
    """Request payload for hybrid or semantic code search."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    commit_sha: CommitSha
    query: str = Field(min_length=1)
    mode: SearchMode = SearchMode.HYBRID
    limit: int = Field(default=20, ge=1, le=100)


class HybridSearchResponse(BaseModel):
    """Response payload for hybrid search."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    commit_sha: CommitSha
    query: str = Field(min_length=1)
    mode: SearchMode
    total_results: int = Field(ge=0)
    results: list[SearchResultItem] = Field(default_factory=list)
