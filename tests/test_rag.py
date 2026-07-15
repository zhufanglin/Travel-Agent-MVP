"""Tests for the RAG module — loader, embeddings, retriever, and integration.

Uses the real knowledge/ directory (shipped with the project).
"""

import tempfile
from pathlib import Path

import pytest

from travel_agent.rag.embeddings import MockEmbedder
from travel_agent.rag.loader import Chunk, load_knowledge_dir
from travel_agent.rag.retriever import KnowledgeRetriever


# ──────────────────────────────────────────────
#  1. Loader Tests
# ──────────────────────────────────────────────


class TestLoader:
    def test_loads_default_knowledge_dir(self):
        """Should load chunks from the default knowledge directory."""
        chunks = load_knowledge_dir()
        assert len(chunks) > 0
        assert all(isinstance(c, Chunk) for c in chunks)

    def test_chunks_have_destination_metadata(self):
        """Each chunk should have a destination extracted from filename."""
        chunks = load_knowledge_dir()
        destinations = {c.destination for c in chunks}
        assert "北京" in destinations
        assert "成都" in destinations
        assert "杭州" in destinations

    def test_chunks_have_section_and_text(self):
        """Chunks should have non-empty section and text content."""
        chunks = load_knowledge_dir()
        for c in chunks[:5]:
            assert c.section, f"Empty section in chunk {c.chunk_id}"
            assert len(c.text) > 5, f"Short text in chunk {c.chunk_id}"

    def test_handles_empty_directory(self):
        """Should return empty list for non-existent directory."""
        chunks = load_knowledge_dir("/nonexistent/path")
        assert chunks == []

    def test_handles_none_directory(self):
        """Should use default when None is passed."""
        chunks = load_knowledge_dir(None)
        assert len(chunks) > 0

    def test_chunk_count(self):
        """Known files should produce expected chunk count."""
        chunks = load_knowledge_dir()
        # 3 files × multiple sections each
        assert 30 <= len(chunks) <= 60


# ──────────────────────────────────────────────
#  2. Embeddings Tests
# ──────────────────────────────────────────────


class TestMockEmbedder:
    def test_consistent_vectors(self):
        """Same text should produce the same embedding vector."""
        emb = MockEmbedder()
        v1 = emb.embed_query("成都美食推荐")
        v2 = emb.embed_query("成都美食推荐")
        assert v1 == v2

    def test_different_texts_different_vectors(self):
        """Different texts should produce different vectors."""
        emb = MockEmbedder()
        v1 = emb.embed_query("北京烤鸭")
        v2 = emb.embed_query("成都火锅")
        assert v1 != v2

    def test_vector_dimension(self):
        """Vectors should have the expected dimension (384)."""
        emb = MockEmbedder()
        vec = emb.embed_query("test")
        assert len(vec) == 384

    def test_batch_embed_documents(self):
        """embed_documents should handle multiple texts."""
        emb = MockEmbedder()
        texts = ["北京", "成都", "杭州"]
        vecs = emb.embed_documents(texts)
        assert len(vecs) == 3
        for v in vecs:
            assert len(v) == 384


# ──────────────────────────────────────────────
#  3. Retriever Tests
# ──────────────────────────────────────────────


class TestKnowledgeRetriever:
    def test_build_index(self):
        """Building the index should load chunks successfully."""
        r = KnowledgeRetriever()
        r.build_index()
        assert r.is_loaded
        assert r.total_chunks > 0

    def test_query_returns_results(self):
        """Querying should return relevant chunks."""
        r = KnowledgeRetriever()
        r.build_index()
        results = r.query("成都")
        assert len(results) > 0
        assert results[0]["destination"] == "成都"

    def test_query_with_destination_filter(self):
        """destination_filter should narrow results."""
        r = KnowledgeRetriever()
        r.build_index()
        results = r.query("美食推荐", k=3, destination_filter="北京")
        assert len(results) > 0
        for res in results:
            assert res["destination"] == "北京"

    def test_query_destination_convenience(self):
        """query_destination should filter by destination."""
        r = KnowledgeRetriever()
        r.build_index()
        results = r.query_destination("杭州", k=2)
        assert len(results) >= 1
        assert all(res["destination"] == "杭州" for res in results)

    def test_results_have_expected_fields(self):
        """Each result should have text, source, destination, section, score."""
        r = KnowledgeRetriever()
        r.build_index()
        results = r.query("北京", k=1)
        res = results[0]
        assert "text" in res
        assert "source" in res
        assert "destination" in res
        assert "section" in res
        assert "score" in res

    def test_query_nonexistent_destination(self):
        """Querying for unknown destination should return empty list."""
        r = KnowledgeRetriever()
        r.build_index()
        results = r.query("未知星球", destination_filter="未知星球")
        assert results == []

    def test_not_loaded_returns_empty(self):
        """Querying without building index should return empty list."""
        r = KnowledgeRetriever()
        assert r.query("test") == []

    def test_pre_built_chunks(self):
        """Should accept pre-loaded chunks."""
        r = KnowledgeRetriever()
        chunks = load_knowledge_dir()
        r.build_index(chunks)
        assert r.is_loaded
        assert r.total_chunks == len(chunks)


# ──────────────────────────────────────────────
#  4. Integration: Researcher → RAG
# ──────────────────────────────────────────────


class TestResearcherRAGIntegration:
    def test_research_report_contains_knowledge(self):
        """Research report warnings should include RAG knowledge."""
        from travel_agent.agents.researcher import researcher_node
        from travel_agent.graph.state import create_initial_state
        from travel_agent.schemas.travel import TravelIntent, TravelPreferences

        intent = TravelIntent(
            destination="成都",
            duration_days=3,
            preferences=TravelPreferences(interests=["attraction", "restaurant"]),
            raw_input="成都3日游",
        )
        state = create_initial_state("成都3日游")
        state["travel_intent"] = intent
        result = researcher_node(state)

        report = result["research_report"]
        assert report is not None
        # Should contain RAG knowledge in warnings
        knowledge_warnings = [w for w in report.warnings if w.startswith("💡")]
        assert len(knowledge_warnings) > 0, (
            f"No RAG knowledge warnings found. Warnings: {report.warnings}"
        )

    def test_rag_tools_in_metadata(self):
        """Research metadata should include rag_retriever."""
        # Reset singleton to force fresh RAG index build for this destination
        import travel_agent.agents.researcher as res
        res._rag = None

        from travel_agent.graph.state import create_initial_state
        from travel_agent.schemas.travel import TravelIntent, TravelPreferences

        intent = TravelIntent(
            destination="北京",
            duration_days=2,
            preferences=TravelPreferences(interests=["attraction"]),
            raw_input="北京2日游",
        )
        state = create_initial_state("北京2日游")
        state["travel_intent"] = intent
        result = res.researcher_node(state)

        meta = result["research_report"].metadata
        assert "rag_retriever" in meta.tools_called, (
            f"rag_retriever not in tools_called: {meta.tools_called}"
        )
