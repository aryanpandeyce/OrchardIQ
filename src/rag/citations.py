"""Citation model and formatter for RAG search results."""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class Citation:
    """Verifiable source citation for RAG retrieved knowledge."""
    source_file: str
    title: str
    category: str
    excerpt: str
    score: float
    doc_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_file": self.source_file,
            "title": self.title,
            "category": self.category,
            "excerpt": self.excerpt,
            "score": round(self.score, 4),
            "doc_id": self.doc_id,
        }

    def format_markdown(self) -> str:
        """Format citation as Markdown badge and link."""
        return f"[[{self.category}] {self.title}]({self.source_file}) (Score: {self.score:.2f})"


def format_citations_block(citations: List[Citation], max_citations: int = 5) -> str:
    """Generate a clean Markdown citations block for agent answers."""
    if not citations:
        return ""

    lines = ["\n### Sources & Citations"]
    for i, c in enumerate(citations[:max_citations], 1):
        lines.append(f"{i}. **{c.title}** (`{c.source_file}`) – *Relevance: {c.score:.2f}*")
        # Trim excerpt to 140 chars
        clean_excerpt = " ".join(c.excerpt.split())[:140] + "..."
        lines.append(f"   > \"{clean_excerpt}\"")

    return "\n".join(lines)
