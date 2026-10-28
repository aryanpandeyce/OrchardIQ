"""Knowledge base parser, chunker, and vector store indexing pipeline."""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.console import Console

from src.config import Settings, settings
from src.rag.vector_store import Document, VectorStore, ChromaVectorStore


class KnowledgeIndexer:
    """Chunks and indexes Markdown documents and support tickets into a VectorStore."""

    def __init__(self, vector_store: VectorStore, config: Optional[Settings] = None):
        self.vector_store = vector_store
        self.config = config or settings

    def index_markdown_docs(self, docs_dir: Path) -> int:
        """Parse, section-chunk, and index all markdown files from the knowledge base."""
        if not docs_dir.exists():
            return 0

        documents: List[Document] = []
        md_files = list(docs_dir.glob("**/*.md"))

        for file_path in md_files:
            rel_path = file_path.relative_to(docs_dir)
            category = rel_path.parts[0] if len(rel_path.parts) > 1 else "general"
            text_content = file_path.read_text(encoding="utf-8")

            # Extract title from first # header or filename
            title_match = re.search(r"^#\s+(.+)$", text_content, re.MULTILINE)
            doc_title = title_match.group(1).strip() if title_match else file_path.stem.replace("_", " ").title()

            # Split document into logical sections by ## headers
            sections = re.split(r"\n(?=##\s+)", text_content)
            for idx, sec in enumerate(sections):
                sec_text = sec.strip()
                if not sec_text:
                    continue

                # Extract section subtitle if present
                sec_title_match = re.search(r"^##\s+(.+)$", sec_text, re.MULTILINE)
                section_title = sec_title_match.group(1).strip() if sec_title_match else "Overview"

                chunk_id = f"doc_{file_path.stem}_{idx}"
                metadata = {
                    "source_file": str(rel_path).replace("\\", "/"),
                    "category": category,
                    "title": doc_title,
                    "section": section_title,
                    "chunk_index": idx,
                    "type": "documentation",
                }

                documents.append(
                    Document(
                        doc_id=chunk_id,
                        text=sec_text,
                        metadata=metadata,
                    )
                )

        return self.vector_store.add_documents(documents)

    def index_support_tickets(self, unstructured_dir: Path, max_tickets: int = 5000) -> int:
        """Parse and index customer support tickets into the vector store."""
        jsonl_path = unstructured_dir / "support_tickets.jsonl"
        if not jsonl_path.exists():
            return 0

        documents: List[Document] = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= max_tickets:
                    break
                line_str = line.strip()
                if not line_str:
                    continue
                ticket = json.loads(line_str)

                text = (
                    f"Support Ticket {ticket.get('ticket_id')}\n"
                    f"Product: {ticket.get('product_id')} | Region: {ticket.get('region_id')} | Category: {ticket.get('category')}\n"
                    f"Subject: {ticket.get('subject')}\n"
                    f"Customer Comment: {ticket.get('customer_comment')}\n"
                    f"Agent Notes: {ticket.get('agent_notes')}\n"
                    f"Component Batch: {ticket.get('component_batch_id')}\n"
                    f"Status: {ticket.get('status')}"
                )

                metadata = {
                    "source_file": "data/unstructured/support_tickets.jsonl",
                    "category": "support_tickets",
                    "ticket_id": ticket.get("ticket_id", ""),
                    "product_id": ticket.get("product_id", ""),
                    "region_id": ticket.get("region_id", ""),
                    "component_batch_id": ticket.get("component_batch_id", "N/A"),
                    "sentiment": ticket.get("sentiment", "Neutral"),
                    "title": f"Support Ticket: {ticket.get('subject')}",
                    "type": "ticket",
                }

                documents.append(
                    Document(
                        doc_id=f"tck_{ticket.get('ticket_id')}",
                        text=text,
                        metadata=metadata,
                    )
                )

        return self.vector_store.add_documents(documents)

    def index_all(self, docs_dir: Optional[Path] = None, unstructured_dir: Optional[Path] = None) -> Dict[str, int]:
        """Index both markdown documentation and support tickets."""
        d_dir = docs_dir or self.config.get_docs_path()
        u_dir = unstructured_dir or self.config.get_unstructured_path()

        doc_count = self.index_markdown_docs(d_dir)
        ticket_count = self.index_support_tickets(u_dir)

        return {
            "markdown_chunks": doc_count,
            "ticket_chunks": ticket_count,
            "total_indexed": doc_count + ticket_count,
        }


def main() -> None:
    """CLI utility to re-index all knowledge into ChromaDB."""
    console = Console()
    console.print("[bold cyan]Initializing ChromaDB Vector Store...[/bold cyan]")
    vs = ChromaVectorStore()
    indexer = KnowledgeIndexer(vs)

    console.print("[yellow]Indexing knowledge base and support tickets...[/yellow]")
    counts = indexer.index_all()

    console.print(f"[bold green]Index Complete![/bold green]")
    console.print(f"  Documentation Chunks: [bold]{counts['markdown_chunks']}[/bold]")
    console.print(f"  Support Ticket Chunks: [bold]{counts['ticket_chunks']}[/bold]")
    console.print(f"  Total Indexed Items: [bold]{counts['total_indexed']}[/bold]")


if __name__ == "__main__":
    main()
