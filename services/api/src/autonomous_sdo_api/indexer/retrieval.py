import math

from autonomous_sdo_api.indexer.embeddings import EmbeddingAdapter
from autonomous_sdo_api.indexer.models import CodeChunk, SearchMode, SearchResultItem


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot = sum(a * b for a, b in zip(vec_a, vec_b, strict=False))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return max(0.0, min(1.0, dot / (norm_a * norm_b)))


def compute_rrf_score(
    lexical_rank: int | None,
    semantic_rank: int | None,
    k: int = 60,
) -> float:
    """Calculate Reciprocal Rank Fusion (RRF) score."""
    score = 0.0
    if lexical_rank is not None:
        score += 1.0 / (k + lexical_rank)
    if semantic_rank is not None:
        score += 1.0 / (k + semantic_rank)
    return score


class HybridSearchEngine:
    """Combines lexical keyword matching with dense vector semantic search using RRF."""

    def __init__(self, rrf_k: int = 60) -> None:
        self.rrf_k = rrf_k

    def _lexical_score(self, query: str, text: str) -> float:
        """Compute simple normalized term frequency score for keyword matching."""
        terms = [t.lower() for t in query.split() if t.strip()]
        if not terms:
            return 0.0

        lower_text = text.lower()
        match_count = sum(lower_text.count(term) for term in terms)
        return float(match_count)

    async def search(
        self,
        query: str,
        chunks: list[CodeChunk],
        chunk_embeddings: dict[str, list[float]],
        embedding_adapter: EmbeddingAdapter,
        mode: SearchMode = SearchMode.HYBRID,
        limit: int = 20,
    ) -> list[SearchResultItem]:
        """Rank and return code chunks matching query under the requested retrieval mode."""
        if not chunks or not query.strip():
            return []

        # 1. Lexical ranking
        lexical_ranked: list[tuple[CodeChunk, float]] = []
        if mode in (SearchMode.LEXICAL, SearchMode.HYBRID):
            scored_lex = []
            for chk in chunks:
                score = self._lexical_score(query, chk.content)
                if score > 0:
                    scored_lex.append((chk, score))
            scored_lex.sort(key=lambda x: x[1], reverse=True)
            lexical_ranked = scored_lex

        lexical_ranks: dict[str, int] = {
            chk.chunk_id: rank for rank, (chk, _) in enumerate(lexical_ranked, start=1)
        }

        # 2. Semantic ranking
        semantic_ranked: list[tuple[CodeChunk, float]] = []
        if mode in (SearchMode.SEMANTIC, SearchMode.HYBRID):
            query_vec = await embedding_adapter.embed_text(query)
            scored_sem = []
            for chk in chunks:
                chk_vec = chunk_embeddings.get(chk.chunk_id)
                if chk_vec:
                    sim = cosine_similarity(query_vec, chk_vec)
                    scored_sem.append((chk, sim))
            scored_sem.sort(key=lambda x: x[1], reverse=True)
            semantic_ranked = scored_sem

        semantic_ranks: dict[str, int] = {
            chk.chunk_id: rank for rank, (chk, _) in enumerate(semantic_ranked, start=1)
        }

        # 3. Fuse scores based on mode
        results: list[SearchResultItem] = []
        chunk_by_id = {chk.chunk_id: chk for chk in chunks}

        if mode == SearchMode.LEXICAL:
            for chk, score in lexical_ranked[:limit]:
                results.append(
                    SearchResultItem(
                        chunk_id=chk.chunk_id,
                        file_path=chk.file_path,
                        start_line=chk.start_line,
                        end_line=chk.end_line,
                        content=chk.content,
                        chunk_type=chk.chunk_type,
                        score=score,
                        lexical_rank=lexical_ranks.get(chk.chunk_id),
                    )
                )
            return results

        if mode == SearchMode.SEMANTIC:
            for chk, score in semantic_ranked[:limit]:
                results.append(
                    SearchResultItem(
                        chunk_id=chk.chunk_id,
                        file_path=chk.file_path,
                        start_line=chk.start_line,
                        end_line=chk.end_line,
                        content=chk.content,
                        chunk_type=chk.chunk_type,
                        score=score,
                        semantic_rank=semantic_ranks.get(chk.chunk_id),
                    )
                )
            return results

        # Hybrid Mode: RRF
        candidate_ids = set(lexical_ranks.keys()) | set(semantic_ranks.keys())
        fused: list[tuple[CodeChunk, float, int | None, int | None]] = []

        for cid in candidate_ids:
            target_chunk = chunk_by_id[cid]
            l_rank = lexical_ranks.get(cid)
            s_rank = semantic_ranks.get(cid)
            rrf_score = compute_rrf_score(l_rank, s_rank, k=self.rrf_k)
            fused.append((target_chunk, rrf_score, l_rank, s_rank))

        fused.sort(key=lambda x: x[1], reverse=True)

        for chk, score, l_rank, s_rank in fused[:limit]:
            results.append(
                SearchResultItem(
                    chunk_id=chk.chunk_id,
                    file_path=chk.file_path,
                    start_line=chk.start_line,
                    end_line=chk.end_line,
                    content=chk.content,
                    chunk_type=chk.chunk_type,
                    score=round(score, 6),
                    lexical_rank=l_rank,
                    semantic_rank=s_rank,
                )
            )

        return results
