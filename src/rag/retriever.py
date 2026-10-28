"""Hybrid retriever combining ChromaDB dense vector search and BM25 sparse keyword search."""

import math
import re
from collections import Counter
from typing import Dict, List, Any, Optional, Tuple

from src.rag.vector_store import VectorStore, SearchResult, Document
from src.rag.citations import Citation


class BM25Index:
    """Lightweight in-memory Okapi BM25 implementation for enterprise keyword retrieval."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_ids: List[str] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freqs: Dict[str, int] = Counter()
        self.corpus_size: int = 0
        self.tokenized_corpus: List[List[str]] = []
        self.doc_map: Dict[str, Document] = {}

    def tokenize(self, text: str) -> List[str]:
        """Tokenize string into alphanumeric tokens, preserving hyphens for batch/SKU tags."""
        return re.findall(r"[a-zA-Z0-9_-]+", text.lower())

    def index_documents(self, documents: List[Document]) -> None:
        """Build BM25 index from a list of Document objects."""
        self.doc_ids = []
        self.doc_lengths = []
        self.tokenized_corpus = []
        self.doc_freqs = Counter()
        self.doc_map = {}
        self.corpus_size = len(documents)

        if self.corpus_size == 0:
            self.avg_doc_len = 0.0
            return

        total_len = 0
        for doc in documents:
            tokens = self.tokenize(doc.text)
            self.doc_ids.append(doc.doc_id)
            self.tokenized_corpus.append(tokens)
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_len += doc_len
            self.doc_map[doc.doc_id] = doc

            unique_tokens = set(tokens)
            for t in unique_tokens:
                self.doc_freqs[t] += 1

        self.avg_doc_len = total_len / self.corpus_size

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Compute BM25 scores for the query and return ranked SearchResult items."""
        if self.corpus_size == 0:
            return []

        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        scores: List[Tuple[float, int]] = []

        for idx, (tokens, doc_len) in enumerate(zip(self.tokenized_corpus, self.doc_lengths)):
            doc_id = self.doc_ids[idx]
            doc = self.doc_map[doc_id]

            # Check filters
            if filters:
                match = True
                for k, v in filters.items():
                    if doc.metadata.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            token_counts = Counter(tokens)
            score = 0.0

            for q in query_tokens:
                if q not in self.doc_freqs:
                    continue
                df = self.doc_freqs[q]
                # Standard Okapi BM25 IDF
                idf = math.log((self.corpus_size - df + 0.5) / (df + 0.5) + 1.0)
                tf = token_counts[q]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / (self.avg_doc_len or 1.0)))
                score += idf * (numerator / denominator)

            if score > 0:
                scores.append((score, idx))

        scores.sort(key=lambda x: x[0], reverse=True)
        results: List[SearchResult] = []

        for score, idx in scores[:top_k]:
            doc_id = self.doc_ids[idx]
            doc = self.doc_map[doc_id]
            # Normalize BM25 score approximately into [0, 1] range
            norm_score = round(1.0 - math.exp(-score / 10.0), 4)
            results.append(
                SearchResult(
                    doc_id=doc_id,
                    text=doc.text,
                    metadata=doc.metadata,
                    score=norm_score,
                )
            )

        return results


class HybridRetriever:
    """
    Hybrid retriever combining dense semantic search (ChromaDB) and
    sparse keyword search (BM25) using Reciprocal Rank Fusion (RRF).
    """

    def __init__(
        self,
        vector_store: VectorStore,
        documents: Optional[List[Document]] = None,
        rrf_k: int = 60,
    ):
        self.vector_store = vector_store
        self.bm25_index = BM25Index()
        self.rrf_k = rrf_k
        if documents:
            self.bm25_index.index_documents(documents)

    def update_bm25_documents(self, documents: List[Document]) -> None:
        """Update or initialize the BM25 sparse keyword index."""
        self.bm25_index.index_documents(documents)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        dense_weight: float = 0.5,
        sparse_weight: float = 0.5,
    ) -> List[Citation]:
        """Execute hybrid search with Reciprocal Rank Fusion and return Citation objects."""
        candidate_multiplier = max(2, top_k * 2)

        # 1. Dense Semantic Search
        dense_results = self.vector_store.search(
            query=query,
            top_k=candidate_multiplier,
            filters=filters,
        )

        # 2. Sparse BM25 Search
        sparse_results = self.bm25_index.search(
            query=query,
            top_k=candidate_multiplier,
            filters=filters,
        )

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {}
        doc_store: Dict[str, SearchResult] = {}

        # Process dense ranks
        for rank, res in enumerate(dense_results):
            doc_id = res.doc_id
            doc_store[doc_id] = res
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (dense_weight / (self.rrf_k + rank + 1))

        # Process sparse ranks
        for rank, res in enumerate(sparse_results):
            doc_id = res.doc_id
            if doc_id not in doc_store:
                doc_store[doc_id] = res
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (sparse_weight / (self.rrf_k + rank + 1))

        # Sort by merged RRF score
        sorted_candidates = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        citations: List[Citation] = []
        for doc_id, rrf_score in sorted_candidates[:top_k]:
            res = doc_store[doc_id]
            meta = res.metadata
            excerpt = res.text[:280].strip()

            citations.append(
                Citation(
                    source_file=meta.get("source_file", "unknown"),
                    title=meta.get("title", meta.get("section", "Knowledge Document")),
                    category=meta.get("category", "general"),
                    excerpt=excerpt,
                    score=float(rrf_score * 100),  # Scale RRF score to human-readable number
                    doc_id=doc_id,
                )
            )

        return citations

    def retrieve_context_str(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Format retrieved documents as a formatted context block for LLM prompts."""
        citations = self.retrieve(query=query, top_k=top_k, filters=filters)
        if not citations:
            return "No relevant enterprise documentation found."

        blocks = []
        for i, c in enumerate(citations, 1):
            blocks.append(
                f"### Document {i}: {c.title} (Category: {c.category})\n"
                f"Source: {c.source_file}\n"
                f"Content Excerpt:\n{c.excerpt}\n"
            )

        return "\n".join(blocks)
