"""Unit and benchmark tests for Phase 2: Catalog & Hybrid RAG Subsystem."""

import json
from pathlib import Path
import pytest

from src.rag.vector_store import ChromaVectorStore, Document
from src.rag.indexer import KnowledgeIndexer
from src.rag.retriever import HybridRetriever, BM25Index
from src.rag.citations import Citation, format_citations_block


@pytest.fixture(scope="module")
def populated_rag_system(tmp_path_factory) -> HybridRetriever:
    """Index knowledge docs and support tickets into an isolated ChromaDB vector store."""
    temp_dir = tmp_path_factory.mktemp("rag_test_")
    vs = ChromaVectorStore(
        collection_name="test_knowledge",
        persist_dir=temp_dir / "chroma",
        in_memory=True,
    )
    indexer = KnowledgeIndexer(vs)

    docs_dir = Path("docs/knowledge_base")
    unstr_dir = Path("data/unstructured")

    # Index real markdown docs from docs/knowledge_base
    indexer.index_markdown_docs(docs_dir)
    # Index support tickets
    indexer.index_support_tickets(unstr_dir, max_tickets=500)

    # Build corpus documents for BM25
    corpus_docs = []
    for file_path in docs_dir.glob("**/*.md"):
        rel_path = file_path.relative_to(docs_dir)
        cat = rel_path.parts[0] if len(rel_path.parts) > 1 else "general"
        text = file_path.read_text(encoding="utf-8")
        corpus_docs.append(
            Document(
                doc_id=f"doc_{file_path.stem}",
                text=text,
                metadata={"source_file": file_path.name, "category": cat, "title": file_path.stem},
            )
        )

    # Add sample tickets to BM25 corpus
    tck_path = unstr_dir / "support_tickets.jsonl"
    if tck_path.exists():
        with open(tck_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= 500:
                    break
                t = json.loads(line)
                corpus_docs.append(
                    Document(
                        doc_id=f"tck_{t.get('ticket_id')}",
                        text=f"{t.get('subject')} {t.get('customer_comment')} {t.get('component_batch_id')} {t.get('agent_notes')}",
                        metadata={"source_file": "support_tickets.jsonl", "category": "support_tickets", "title": t.get("subject")},
                    )
                )

    retriever = HybridRetriever(vector_store=vs, documents=corpus_docs)
    return retriever


def test_vector_store_crud():
    """Assert VectorStore adds, retrieves, counts, and clears documents."""
    vs = ChromaVectorStore(collection_name="crud_test", in_memory=True)
    assert vs.count() == 0

    docs = [
        Document("d1", "PearPhone battery life is optimized with silicon power management.", {"category": "hardware"}),
        Document("d2", "Net Revenue is computed by subtracting discounts from gross proceeds.", {"category": "finance"}),
    ]
    added = vs.add_documents(docs)
    assert added == 2
    assert vs.count() == 2

    # Similarity search
    results = vs.search("battery efficiency", top_k=1)
    assert len(results) == 1
    assert results[0].doc_id == "d1"
    assert results[0].score > 0.0

    # Clear
    vs.clear()
    assert vs.count() == 0


def test_bm25_exact_keyword_matching():
    """Assert BM25 locates exact technical terms and identifiers like batch IDs."""
    bm25 = BM25Index()
    docs = [
        Document("d1", "General warranty repairs at retail stores.", {"type": "info"}),
        Document("d2", "Severe thermal swelling discovered in component lot BP-2025-08 cathode cells.", {"type": "incident"}),
        Document("d3", "Firmware version v14.2 introduces DisplayPort clock sync timing regressions.", {"type": "incident"}),
    ]
    bm25.index_documents(docs)

    # Search for exact batch tag
    res = bm25.search("BP-2025-08", top_k=1)
    assert len(res) == 1
    assert res[0].doc_id == "d2"

    # Search for firmware patch string
    res2 = bm25.search("v14.2 DisplayPort", top_k=1)
    assert len(res2) == 1
    assert res2[0].doc_id == "d3"


def test_hybrid_retrieval_rrf(populated_rag_system: HybridRetriever):
    """Assert HybridRetriever merges dense and sparse results with citations."""
    query = "What caused the claims spike for PearPhone 16 Pro in APAC during Q3?"
    citations = populated_rag_system.retrieve(query=query, top_k=3)

    assert len(citations) > 0
    top_citation = citations[0]
    assert isinstance(top_citation, Citation)
    assert top_citation.score > 0.0
    assert any("2025-q3-apac-battery-claims-spike" in c.source_file or "battery" in c.excerpt.lower() for c in citations)


def test_metadata_filtering(populated_rag_system: HybridRetriever):
    """Assert metadata filtering limits results strictly to specified categories."""
    citations = populated_rag_system.retrieve(
        query="revenue and financial metrics",
        top_k=5,
        filters={"category": "business_glossary"},
    )
    assert len(citations) > 0
    for c in citations:
        assert c.category == "business_glossary"


def test_citations_formatting():
    """Assert citations block produces formatted markdown output."""
    citations = [
        Citation("docs/net_revenue.md", "Net Revenue", "business_glossary", "Gross revenue minus discounts.", 0.95, "c1"),
        Citation("docs/attach_rate.md", "Attach Rate", "business_glossary", "Watch units divided by phone units.", 0.88, "c2"),
    ]
    block = format_citations_block(citations)
    assert "### Sources & Citations" in block
    assert "Net Revenue" in block
    assert "docs/net_revenue.md" in block


def test_retrieval_golden_set_hit_rate(populated_rag_system: HybridRetriever):
    """
    RAG Benchmark Eval:
    Evaluate Hit-Rate@3 across the 12 golden test questions.
    Assert Hit-Rate@3 >= 85%.
    """
    golden_path = Path("evals/retrieval_golden_set.json")
    assert golden_path.exists()

    with open(golden_path, "r", encoding="utf-8") as f:
        golden_set = json.load(f)

    hits_at_3 = 0
    total = len(golden_set)

    for item in golden_set:
        query = item["query"]
        expected_files = item.get("expected_files", [])
        expected_keywords = item.get("expected_keywords", [])

        citations = populated_rag_system.retrieve(query=query, top_k=3)
        retrieved_files = [Path(c.source_file).name for c in citations]
        retrieved_text = " ".join([c.excerpt for c in citations])

        # Check file match or keyword match in top-3 citations
        file_hit = any(exp in retrieved_files for exp in expected_files)
        keyword_hit = any(kw.lower() in retrieved_text.lower() for kw in expected_keywords)

        if file_hit or keyword_hit:
            hits_at_3 += 1

    hit_rate = (hits_at_3 / total) * 100.0
    print(f"\nRAG Evaluation Result: Hit-Rate@3 = {hit_rate:.1f}% ({hits_at_3}/{total})")

    assert hit_rate >= 85.0, f"Hit-Rate@3 ({hit_rate}%) is below 85% requirement!"
