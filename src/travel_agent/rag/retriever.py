"""FAISS retriever — builds a vector index over knowledge chunks and
retrieves the most relevant ones for a given query.

Usage:
    retriever = KnowledgeRetriever()
    retriever.build_index()            # load + chunk + embed
    results = retriever.query("火锅推荐", k=3)
"""

import tempfile
from pathlib import Path
from typing import Optional

import faiss
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from travel_agent.rag.embeddings import get_embedder
from travel_agent.rag.loader import load_knowledge_dir


class KnowledgeRetriever:
    """FAISS-powered retriever for travel knowledge documents.

    Loads markdown knowledge docs, chunks them, builds a FAISS index,
    and provides query() for similarity search.
    """

    def __init__(self, knowledge_dir: Optional[str | Path] = None):
        self._embedder = get_embedder()
        self._vector_store: Optional[FAISS] = None
        self._knowledge_dir = knowledge_dir
        self._total_chunks = 0

    @property
    def is_loaded(self) -> bool:
        """Whether the index has been built."""
        return self._vector_store is not None

    @property
    def total_chunks(self) -> int:
        return self._total_chunks

    def build_index(self, chunks: Optional[list] = None) -> None:
        """Build the FAISS index from knowledge chunks.

        Args:
            chunks: Optional pre-loaded chunks. If None, loads from disk.
        """
        if chunks is None:
            chunks = load_knowledge_dir(self._knowledge_dir)

        if not chunks:
            self._total_chunks = 0
            return

        docs = [
            Document(
                page_content=c.text,
                metadata={
                    "source": c.source,
                    "destination": c.destination,
                    "section": c.section,
                    "chunk_id": c.chunk_id,
                },
            )
            for c in chunks
        ]

        # Build FAISS index in memory
        self._vector_store = FAISS.from_documents(docs, self._embedder)
        self._total_chunks = len(chunks)

    def query(self, text: str, k: int = 3, destination_filter: Optional[str] = None) -> list[dict]:
        """Retrieve top-k knowledge chunks relevant to the query.

        Args:
            text: Query text (e.g. "成都美食推荐").
            k: Number of chunks to return.
            destination_filter: If set, only return chunks for this destination.

        Returns:
            List of dicts: {text, source, destination, section, score}.
        """
        if not self._vector_store:
            return []

        # Search with score
        # When filtering by destination, search all chunks so the filter is effective
        # even with mock embeddings (low-quality similarity)
        search_k = self._total_chunks if destination_filter else k * 3
        docs_with_scores = self._vector_store.similarity_search_with_score(text, k=search_k)

        results = []
        for doc, score in docs_with_scores:
            dest = doc.metadata.get("destination", "")
            if destination_filter and dest and dest != destination_filter:
                continue
            results.append({
                "text": doc.page_content,
                "source": doc.metadata.get("source", ""),
                "destination": dest,
                "section": doc.metadata.get("section", ""),
                "score": float(score),
            })
            if len(results) >= k:
                break

        return results

    def query_destination(self, destination: str, k: int = 3) -> list[dict]:
        """Convenience: query knowledge for a specific destination.

        Args:
            destination: City name in Chinese, e.g. "成都".
            k: Number of chunks to return.

        Returns:
            List of dicts with knowledge chunks.
        """
        return self.query(destination, k=k, destination_filter=destination)
