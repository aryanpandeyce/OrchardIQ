"""RAG and knowledge catalog subsystem for OrchardIQ."""

from src.rag.vector_store import (
    VectorStore,
    ChromaVectorStore,
    Document,
    SearchResult,
    LightweightEmbeddingFunction,
)
from src.rag.indexer import KnowledgeIndexer
from src.rag.retriever import HybridRetriever, BM25Index
from src.rag.citations import Citation, format_citations_block

__all__ = [
    "VectorStore",
    "ChromaVectorStore",
    "Document",
    "SearchResult",
    "LightweightEmbeddingFunction",
    "KnowledgeIndexer",
    "HybridRetriever",
    "BM25Index",
    "Citation",
    "format_citations_block",
]
