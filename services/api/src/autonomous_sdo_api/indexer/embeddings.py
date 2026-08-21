import hashlib
import math
from abc import ABC, abstractmethod
from typing import Any

import httpx


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0.0:
        return vec
    return [x / norm for x in vec]


class EmbeddingAdapter(ABC):
    """Abstract provider adapter for computing text embeddings."""

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Vector dimensions produced by this embedding model."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name/identifier of the embedding model."""

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text string."""

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of text strings."""


class MockEmbeddingAdapter(EmbeddingAdapter):
    """Deterministic, provider-neutral mock embedding adapter for testing and offline execution."""

    def __init__(self, dimensions: int = 384, model_name: str = "mock-bge-m3") -> None:
        self._dimensions = dimensions
        self._model_name = model_name

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model_name(self) -> str:
        return self._model_name

    def _generate_vector(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vec: list[float] = []
        for i in range(self._dimensions):
            byte_val = digest[i % len(digest)]
            val = (byte_val - 128.0) / 128.0 + (i * 0.001)
            vec.append(val)
        return _l2_normalize(vec)

    async def embed_text(self, text: str) -> list[float]:
        return self._generate_vector(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self._generate_vector(t) for t in texts]


class OpenAiEmbeddingAdapter(EmbeddingAdapter):
    """Embedding adapter for OpenAI-compatible embedding endpoints (including vLLM/TEI)."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model_name: str = "text-embedding-3-small",
        dimensions: int = 1536,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model_name = model_name
        self._dimensions = dimensions
        self._client = client
        self._owns_client = client is None

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model_name(self) -> str:
        return self._model_name

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        client = self._get_client()
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self._model_name,
            "input": texts,
        }

        response = await client.post(
            f"{self._base_url}/embeddings",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        embeddings_data = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in embeddings_data]

    async def embed_text(self, text: str) -> list[float]:
        results = await self.embed_batch([text])
        return results[0]


def get_embedding_adapter(
    provider: str = "mock",
    api_key: str | None = None,
    base_url: str | None = None,
    model_name: str | None = None,
) -> EmbeddingAdapter:
    """Factory to instantiate embedding provider adapters."""
    p_lower = provider.lower()
    if p_lower == "mock":
        return MockEmbeddingAdapter(model_name=model_name or "mock-bge-m3")

    if p_lower in ("openai", "vllm", "tei"):
        if not api_key:
            return MockEmbeddingAdapter()
        return OpenAiEmbeddingAdapter(
            api_key=api_key,
            base_url=base_url or "https://api.openai.com/v1",
            model_name=model_name or "text-embedding-3-small",
        )

    return MockEmbeddingAdapter()
