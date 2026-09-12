"""
Sanity check for the index built by chunk_and_embed.py.

This is deliberately the smallest possible test: embed a question, ask
Chroma for the closest matches, print them. No LLM, no prompt template,
nothing else in the pipeline yet. The reason to run this BEFORE building
the retriever/generator files: if something's wrong with chunking or
embedding, you want to find out here — with a small, isolated test —
not three files later when a bad answer could be a retrieval problem,
a prompting problem, or a Gemini problem and you can't tell which.

Run:
    python src/query_test.py "your test question here"
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from rich.console import Console
from rich.table import Table

from src.services.vector_store import get_vector_store

console = Console()


def run_query(question: str, k: int = 5):
    vector_store = get_vector_store()

    # similarity_search_with_score returns (Document, distance) pairs.
    # Note: this is a DISTANCE, not a similarity — lower number = closer
    # match. Don't read it backwards when eyeballing results.
    results = vector_store.similarity_search_with_score(question, k=k)

    if not results:
        console.print(
            "[bold red]No results returned.[/bold red] Check that "
            "chunk_and_embed.py actually ran and populated chroma_db/ "
            "before debugging anything else."
        )
        return

    table = Table(title=f'Top {k} matches for: "{question}"')
    table.add_column("CVE ID", style="cyan")
    table.add_column("Distance", style="magenta")
    table.add_column("CWE")
    table.add_column("CVSS")
    table.add_column("Description", overflow="fold")

    for doc, score in results:
        meta = doc.metadata
        table.add_row(
            meta.get("cve_id", "?"),
            f"{score:.4f}",
            str(meta.get("cwe", "N/A")),
            str(meta.get("cvss_score", "N/A")),
            doc.page_content[:120] + "...",
        )

    console.print(table)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        console.print('[yellow]Usage:[/yellow] python src/query_test.py "your question"')
        sys.exit(1)

    run_query(" ".join(sys.argv[1:]))