from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from autonomous_sdo_api.database.tenancy import OrganizationContext, get_organization_context
from autonomous_sdo_api.indexer.chunking import chunk_file
from autonomous_sdo_api.indexer.embeddings import MockEmbeddingAdapter
from autonomous_sdo_api.indexer.models import (
    FileSymbolsResponse,
    HybridSearchRequest,
    HybridSearchResponse,
)
from autonomous_sdo_api.indexer.retrieval import HybridSearchEngine
from autonomous_sdo_api.indexer.service import SymbolExtractionService
from autonomous_sdo_api.policy import Action, AuthorizationPolicy
from autonomous_sdo_api.repository.models import (
    FileContentResponse,
    FileTreeResponse,
    LexicalSearchResult,
    PathTraversalError,
    RepositoryError,
)
from autonomous_sdo_api.repository.service import RepositoryExplorerService

router = APIRouter(prefix="/api/v1/repositories", tags=["Repositories"])

_AUTH_POLICY = AuthorizationPolicy()
_SYMBOL_SERVICE = SymbolExtractionService()
_SEARCH_ENGINE = HybridSearchEngine()
_EMBED_ADAPTER = MockEmbeddingAdapter()


def get_repo_explorer_service() -> RepositoryExplorerService:
    return RepositoryExplorerService()


@router.get(
    "/tree",
    response_model=FileTreeResponse,
    summary="Get repository file tree",
)
async def get_tree(
    commit_sha: Annotated[str, Query(min_length=40, max_length=64)],
    subpath: Annotated[str, Query()] = "",
    context: Annotated[OrganizationContext, Depends(get_organization_context)] = None,  # type: ignore[assignment]
    service: Annotated[RepositoryExplorerService, Depends(get_repo_explorer_service)] = None,  # type: ignore[assignment]
) -> FileTreeResponse:
    _AUTH_POLICY.require(context.roles, Action.READ_REPOSITORY)
    base_dir = Path.cwd()

    try:
        entries = service.get_file_tree(base_dir, subpath)
        return FileTreeResponse(
            commit_sha=commit_sha,
            path=subpath,
            entries=entries,
        )
    except PathTraversalError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid path: {err}",
        ) from err
    except RepositoryError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err


@router.get(
    "/blob",
    response_model=FileContentResponse,
    summary="Get file content at commit",
)
async def get_blob(
    commit_sha: Annotated[str, Query(min_length=40, max_length=64)],
    file_path: Annotated[str, Query(min_length=1)],
    context: Annotated[OrganizationContext, Depends(get_organization_context)] = None,  # type: ignore[assignment]
    service: Annotated[RepositoryExplorerService, Depends(get_repo_explorer_service)] = None,  # type: ignore[assignment]
) -> FileContentResponse:
    _AUTH_POLICY.require(context.roles, Action.READ_REPOSITORY)
    base_dir = Path.cwd()
    try:
        return service.get_file_blob(base_dir, file_path, commit_sha)
    except PathTraversalError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid path: {err}",
        ) from err
    except RepositoryError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err


@router.get(
    "/search",
    response_model=LexicalSearchResult,
    summary="Lexical search across repository files",
)
async def search_files(
    commit_sha: Annotated[str, Query(min_length=40, max_length=64)],
    query: Annotated[str, Query(min_length=1)],
    context: Annotated[OrganizationContext, Depends(get_organization_context)] = None,  # type: ignore[assignment]
    service: Annotated[RepositoryExplorerService, Depends(get_repo_explorer_service)] = None,  # type: ignore[assignment]
) -> LexicalSearchResult:
    _AUTH_POLICY.require(context.roles, Action.READ_REPOSITORY)
    base_dir = Path.cwd()
    matches = service.search_lexical(base_dir, query)
    return LexicalSearchResult(
        commit_sha=commit_sha,
        query=query,
        total_matches=len(matches),
        matches=matches,
    )


@router.get(
    "/symbols",
    response_model=FileSymbolsResponse,
    summary="Extract AST symbols from a file at commit",
)
async def get_symbols(
    commit_sha: Annotated[str, Query(min_length=40, max_length=64)],
    file_path: Annotated[str, Query(min_length=1)],
    context: Annotated[OrganizationContext, Depends(get_organization_context)] = None,  # type: ignore[assignment]
    service: Annotated[RepositoryExplorerService, Depends(get_repo_explorer_service)] = None,  # type: ignore[assignment]
) -> FileSymbolsResponse:
    _AUTH_POLICY.require(context.roles, Action.READ_REPOSITORY)
    base_dir = Path.cwd()
    try:
        blob = service.get_file_blob(base_dir, file_path, commit_sha)
        if blob.is_binary:
            return FileSymbolsResponse(
                commit_sha=commit_sha,
                file_path=file_path,
                language="binary",
                symbols=[],
            )
        return _SYMBOL_SERVICE.extract_symbols(file_path, blob.content, commit_sha)
    except PathTraversalError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid path: {err}",
        ) from err
    except RepositoryError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err


@router.post(
    "/search/hybrid",
    response_model=HybridSearchResponse,
    summary="Perform hybrid lexical + semantic search",
)
async def search_hybrid(
    request: HybridSearchRequest,
    context: Annotated[OrganizationContext, Depends(get_organization_context)] = None,  # type: ignore[assignment]
) -> HybridSearchResponse:
    _AUTH_POLICY.require(context.roles, Action.READ_REPOSITORY)
    base_dir = Path.cwd()

    # Collect chunks across text source files
    all_chunks = []
    chunk_embeddings = {}

    sample_files = ["README.md", "services/api/pyproject.toml", "packages/contracts/package.json"]
    for rel_path in sample_files:
        f_path = base_dir / rel_path
        if f_path.exists() and f_path.is_file():
            try:
                content = f_path.read_text(encoding="utf-8", errors="ignore")
                chunks = chunk_file(rel_path, content)
                for chk in chunks:
                    all_chunks.append(chk)
                    vec = await _EMBED_ADAPTER.embed_text(chk.content)
                    chunk_embeddings[chk.chunk_id] = vec
            except Exception:  # noqa: S110
                pass

    results = await _SEARCH_ENGINE.search(
        query=request.query,
        chunks=all_chunks,
        chunk_embeddings=chunk_embeddings,
        embedding_adapter=_EMBED_ADAPTER,
        mode=request.mode,
        limit=request.limit,
    )

    return HybridSearchResponse(
        commit_sha=request.commit_sha,
        query=request.query,
        mode=request.mode,
        total_results=len(results),
        results=results,
    )
