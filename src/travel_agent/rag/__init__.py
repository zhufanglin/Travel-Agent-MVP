"""RAG module — Retrieval-Augmented Generation for travel knowledge.

Architecture:
  loader.py     → Load & chunk Markdown knowledge documents
  embeddings.py → Embedding provider (OpenAI or mock)
  retriever.py  → FAISS vector store + query interface

Used by: Researcher Agent to enrich research with local knowledge.
"""
