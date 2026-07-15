"""Embedding provider for RAG.

Supports real OpenAI embeddings (when API key is available) and a
deterministic mock fallback (for testing / no-API scenarios).
"""

import hashlib
import os
from typing import Optional

import numpy as np
from langchain_openai import OpenAIEmbeddings

from travel_agent.config import settings

# ── Embedding dimension ──
_EMBED_DIM = 384  # matches text-embedding-3-small's min dimension


def get_embedder() -> OpenAIEmbeddings:
    """Get a configured OpenAI embedding model.

    Falls back to MockEmbedder if no API key is available.
    """
    api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
    if api_key:
        return OpenAIEmbeddings(
            model="text-embedding-3-small",
            dimensions=_EMBED_DIM,
            api_key=api_key,
        )

    return MockEmbedder()


# ── Mock embedder (deterministic, no API key needed) ──


class MockEmbedder(OpenAIEmbeddings):
    """Hash-based mock embedder for testing / no-API scenarios.

    Produces deterministic vectors from text content using MD5 hash.
    Satisfies the OpenAIEmbeddings interface so FAISS integration works.
    """

    def __init__(self, **kwargs):
        # Skip OpenAI init — we don't need real API calls
        super().__init__(model="text-embedding-3-small", dimensions=_EMBED_DIM, api_key="mock", **kwargs)
        self._mock_mode = True

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._mock_embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._mock_embed(text)

    def _mock_embed(self, text: str) -> list[float]:
        """Deterministic hash-based embedding vector."""
        hash_bytes = hashlib.md5(text.encode("utf-8")).digest()
        # Expand the 16 hash bytes into a 384-dim vector
        vec = np.frombuffer(hash_bytes * 24, dtype=np.uint8)[:_EMBED_DIM].astype(np.float32)
        vec = (vec - 128.0) / 128.0  # normalize to [-1, 1]
        return vec.tolist()
