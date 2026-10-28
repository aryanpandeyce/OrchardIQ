"""Vector store interface and ChromaDB provider implementation."""

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np

try:
    import chromadb
    from chromadb.api.models.Collection import Collection
    from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
except ImportError:
    chromadb = None
    Collection = Any
    class EmbeddingFunction:
        pass
    Documents = List[str]
    Embeddings = List[List[float]]


@dataclass
class Document:
    """Represents a text chunk with metadata in the vector store."""
    doc_id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None


@dataclass
class SearchResult:
    """SearchResult returned by a vector store query."""
    doc_id: str
    text: str
    metadata: Dict[str, Any]
    score: float


class LightweightEmbeddingFunction(EmbeddingFunction):
    """
    Deterministic, fast embedding function for offline demo mode and CI testing.
    Uses SHA-256 word feature hashing with L2-normalization (384 dimensions).
    """

    def __init__(self, dim: int = 384):
        self.dim = dim

    def name(self) -> str:
        return "lightweight_embedding"

    def __call__(self, input: Documents) -> Embeddings:
        embeddings: List[List[float]] = []
        for text in input:
            vec = np.zeros(self.dim, dtype=np.float32)
            words = text.lower().split()
            if not words:
                embeddings.append(vec.tolist())
                continue
            for w in words:
                h = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16)
                idx = h % self.dim
                sign = 1.0 if ((h >> 8) & 1) else -1.0
                vec[idx] += sign
            norm = np.linalg.norm(vec)
            if norm > 1e-6:
                vec /= norm
            embeddings.append(vec.tolist())
        return embeddings


class VectorStore(ABC):
    """Abstract interface for vector store implementations (ChromaDB, pgvector)."""

    @abstractmethod
    def add_documents(self, documents: List[Document]) -> int:
        """Insert or update documents in the collection."""
        pass

    @abstractmethod
    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Perform semantic similarity search with optional metadata filters."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Return total document count in the collection."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all documents from the collection."""
        pass


class ChromaVectorStore(VectorStore):
    """ChromaDB implementation of the VectorStore interface."""

    def __init__(
        self,
        collection_name: str = "orchard_knowledge",
        persist_dir: Optional[Path] = None,
        in_memory: bool = False,
    ):
        if chromadb is None:
            raise ImportError("chromadb is required. Install via pip install chromadb.")

        self.collection_name = collection_name
        self.embedding_fn = LightweightEmbeddingFunction()

        if in_memory:
            self.client = chromadb.Client()
        else:
            storage_path = str(persist_dir or Path("data/chroma"))
            Path(storage_path).mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(path=storage_path)

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(self, documents: List[Document]) -> int:
        if not documents:
            return 0

        # Chunk batch additions into sizes of 500
        batch_size = 500
        total_added = 0

        for i in range(0, len(documents), batch_size):
            chunk = documents[i : i + batch_size]
            ids = [doc.doc_id for doc in chunk]
            documents_text = [doc.text for doc in chunk]
            metadatas = [doc.metadata for doc in chunk]

            self.collection.upsert(
                ids=ids,
                documents=documents_text,
                metadatas=metadatas,
            )
            total_added += len(chunk)

        return total_added

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        where_clause = None
        if filters:
            # Flatten or format single/multi filters for ChromaDB
            if len(filters) == 1:
                k, v = next(iter(filters.items()))
                where_clause = {k: {"$eq": v}}
            else:
                where_clause = {"$and": [{k: {"$eq": v}} for k, v in filters.items()]}

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_clause,
        )

        search_results: List[SearchResult] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return search_results

        ids = results["ids"][0]
        docs = results["documents"][0] if results["documents"] else [""] * len(ids)
        metas = results["metadatas"][0] if results["metadatas"] else [{}] * len(ids)
        distances = results["distances"][0] if results["distances"] else [0.0] * len(ids)

        for doc_id, text, meta, dist in zip(ids, docs, metas, distances):
            # Convert cosine distance to similarity score
            score = round(max(0.0, 1.0 - float(dist)), 4)
            search_results.append(
                SearchResult(
                    doc_id=doc_id,
                    text=text,
                    metadata=meta,
                    score=score,
                )
            )

        return search_results

    def count(self) -> int:
        return self.collection.count()

    def clear(self) -> None:
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
