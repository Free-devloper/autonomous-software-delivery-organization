import math
from uuid import UUID

import httpx
import pytest
from fastapi.testclient import TestClient

from autonomous_sdo_api.app import create_app
from autonomous_sdo_api.config import Settings
from autonomous_sdo_api.database.tenancy import OrganizationContext, get_organization_context
from autonomous_sdo_api.indexer import (
    ChunkType,
    CodeChunk,
    HybridSearchEngine,
    MockEmbeddingAdapter,
    OpenAiEmbeddingAdapter,
    SearchMode,
    chunk_code,
    chunk_file,
    chunk_markdown,
    compute_rrf_score,
    cosine_similarity,
    get_embedding_adapter,
)
from autonomous_sdo_api.policy import Role

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Chunking Tests
# ---------------------------------------------------------------------------


def test_chunk_code() -> None:
    code = "\n".join([f"line_{i} = {i}" for i in range(100)])
    chunks = chunk_code("src/calc.py", code, max_lines=40, overlap_lines=10)

    assert len(chunks) == 3
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 40
    assert chunks[0].chunk_type == ChunkType.CODE
    assert chunks[0].file_path == "src/calc.py"

    assert chunks[1].start_line == 31
    assert chunks[1].end_line == 70

    assert chunk_code("empty.py", "") == []


def test_chunk_markdown() -> None:
    doc = """# ASDO Platform

ASDO is an autonomous software organization.

## Architecture

The system uses a modular monorepo architecture.

### Database

PostgreSQL with pgvector and RLS.
"""
    chunks = chunk_markdown("docs/arch.md", doc)
    assert len(chunks) == 3
    assert chunks[0].chunk_type == ChunkType.DOC
    assert "# ASDO Platform" in chunks[0].content
    assert "## Architecture" in chunks[1].content
    assert "### Database" in chunks[2].content

    assert chunk_markdown("empty.md", "") == []


def test_chunk_file_dispatch() -> None:
    chunks_doc = chunk_file("README.md", "# Title\n\nBody")
    assert chunks_doc[0].chunk_type == ChunkType.DOC

    chunks_code = chunk_file("app.py", "x = 1\ny = 2")
    assert chunks_code[0].chunk_type == ChunkType.CODE


# ---------------------------------------------------------------------------
# Embedding Adapter Tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_mock_embedding_adapter() -> None:
    adapter = MockEmbeddingAdapter(dimensions=128)
    assert adapter.dimensions == 128
    assert adapter.model_name == "mock-bge-m3"

    vec1 = await adapter.embed_text("authentication flow")
    vec2 = await adapter.embed_text("authentication flow")
    vec3 = await adapter.embed_text("database schema")

    assert len(vec1) == 128
    assert vec1 == vec2
    assert vec1 != vec3

    # Check unit normalization
    norm = math.sqrt(sum(x * x for x in vec1))
    assert math.isclose(norm, 1.0, rel_tol=1e-4)

    batch = await adapter.embed_batch(["alpha", "beta"])
    assert len(batch) == 2


@pytest.mark.anyio
async def test_openai_embedding_adapter() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert "/embeddings" in request.url.path
        assert request.headers.get("Authorization") == "Bearer test-key"
        return httpx.Response(
            200,
            json={
                "data": [
                    {"index": 0, "embedding": [0.1, 0.2, 0.3]},
                    {"index": 1, "embedding": [0.4, 0.5, 0.6]},
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        transport=transport, base_url="https://api.openai.com/v1"
    ) as client:
        adapter = OpenAiEmbeddingAdapter(api_key="test-key", client=client)
        assert adapter.dimensions == 1536

        vec = await adapter.embed_text("test input")
        assert vec == [0.1, 0.2, 0.3]

        batch = await adapter.embed_batch(["first", "second"])
        assert len(batch) == 2

        assert await adapter.embed_batch([]) == []


def test_get_embedding_adapter_factory() -> None:
    mock_ad = get_embedding_adapter("mock")
    assert isinstance(mock_ad, MockEmbeddingAdapter)

    openai_ad = get_embedding_adapter("openai", api_key="secret")
    assert isinstance(openai_ad, OpenAiEmbeddingAdapter)

    openai_no_key = get_embedding_adapter("openai")
    assert isinstance(openai_no_key, MockEmbeddingAdapter)


# ---------------------------------------------------------------------------
# Cosine Similarity & RRF Score Tests
# ---------------------------------------------------------------------------


def test_cosine_similarity() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert cosine_similarity([], []) == 0.0
    assert cosine_similarity([1.0], [1.0, 2.0]) == 0.0
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_compute_rrf_score() -> None:
    score1 = compute_rrf_score(1, 1, k=60)
    score_lex_only = compute_rrf_score(1, None, k=60)
    score_sem_only = compute_rrf_score(None, 1, k=60)

    assert score1 > score_lex_only
    assert score_lex_only == score_sem_only
    assert compute_rrf_score(None, None) == 0.0


# ---------------------------------------------------------------------------
# Hybrid Search Engine Tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_hybrid_search_engine() -> None:
    engine = HybridSearchEngine(rrf_k=60)
    adapter = MockEmbeddingAdapter(dimensions=64)

    chunk1 = CodeChunk(
        chunk_id="chk1",
        file_path="auth.py",
        start_line=1,
        end_line=10,
        content="def verify_password(pw: str) -> bool: return True",
        content_hash="h1",
        chunk_type=ChunkType.CODE,
    )
    chunk2 = CodeChunk(
        chunk_id="chk2",
        file_path="db.py",
        start_line=1,
        end_line=10,
        content="def connect_database(): pass",
        content_hash="h2",
        chunk_type=ChunkType.CODE,
    )

    chunks = [chunk1, chunk2]
    embeddings = {
        "chk1": await adapter.embed_text(chunk1.content),
        "chk2": await adapter.embed_text(chunk2.content),
    }

    # Lexical search
    res_lex = await engine.search(
        "verify_password", chunks, embeddings, adapter, mode=SearchMode.LEXICAL
    )
    assert len(res_lex) == 1
    assert res_lex[0].chunk_id == "chk1"

    # Semantic search
    res_sem = await engine.search(
        "authentication", chunks, embeddings, adapter, mode=SearchMode.SEMANTIC
    )
    assert len(res_sem) > 0

    # Hybrid search
    res_hybrid = await engine.search(
        "password", chunks, embeddings, adapter, mode=SearchMode.HYBRID
    )
    assert len(res_hybrid) > 0
    assert res_hybrid[0].score > 0.0

    # Empty cases
    assert await engine.search("", chunks, embeddings, adapter) == []
    assert await engine.search("query", [], embeddings, adapter) == []


# ---------------------------------------------------------------------------
# Hybrid Search Route Tests
# ---------------------------------------------------------------------------


def test_hybrid_search_route() -> None:
    settings = Settings(service_name="asdo-search-test")
    app = create_app(settings=settings)
    client = TestClient(app)
    sha = "7" * 40

    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        organization_id=UUID("018f0000-0000-7000-8000-000000000001"),
        actor_id="usr-search-1",
        roles=frozenset({Role.REPOSITORY_MAINTAINER}),
    )

    res = client.post(
        "/api/v1/repositories/search/hybrid",
        json={
            "commit_sha": sha,
            "query": "ASDO",
            "mode": "hybrid",
            "limit": 5,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["commit_sha"] == sha
    assert data["mode"] == "hybrid"
    assert data["total_results"] >= 0
