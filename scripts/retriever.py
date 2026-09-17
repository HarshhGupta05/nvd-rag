"""
Retriever: the single function every future caller (CLI, eval script,
generator) uses to get relevant CVE chunks for a question. Nothing here
calls Gemini — this file's only job is "given a question, return the
right Documents." Keeping that boundary clean means a bad answer later
is easy to isolate: if retrieval returns the right chunks and the answer
is still wrong, the bug is in prompting/generation, not here.

Why this file exists separately from query_test.py, even though they
look similar: query_test.py is a disposable manual sanity check you run
by hand and read with your eyes. retrieve() is a function other code
imports and calls programmatically. Conflating them would mean either
the generator ends up importing a script meant for eyeballing, or you
end up maintaining print-formatting logic inside your actual pipeline.

The ID-lookup shortcut below exists because of what you just observed:
querying "CVE-2025-55086" through pure semantic search did NOT return
that CVE in the top 5. An ID string has no real semantic content to
match against prose descriptions — so this checks for a CVE-ID pattern
first and does an exact metadata filter instead of embedding search
whenever one is found.
"""
import re
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from langchain_core.documents import Document

from src.services.vector_store import get_vector_store

CVE_ID_PATTERN = re.compile(r"CVE-\d{4}-\d{4,}", re.IGNORECASE)


def _extract_cve_id(question: str) -> str | None:
    match = CVE_ID_PATTERN.search(question)
    return match.group(0).upper() if match else None


def retrieve(question: str, k: int = 5) -> list[Document]:
    """
    Return the k most relevant CVE Documents for a question.

    Two paths:
    - If the question contains a literal CVE ID, fetch that exact record
      via metadata filter (Chroma's .get(), not similarity search).
    - Otherwise, fall back to semantic similarity search.

    Both paths return the same type (list[Document]) so callers don't
    need to know or care which path was taken.
    """
    vector_store = get_vector_store()

    cve_id = _extract_cve_id(question)
    if cve_id:
        result = vector_store.get(where={"cve_id": cve_id}, include=["documents", "metadatas"])
        if result["ids"]:
            # Rebuild Document objects from the raw get() response —
            # .get() returns dicts, not Document objects, unlike similarity_search.
            docs = [
                Document(page_content=doc, metadata=meta)
                for doc, meta in zip(result["documents"], result["metadatas"])
            ]
            return docs
        # Fall through to semantic search if the exact ID isn't in the
        # index (e.g. a typo, or a CVE outside your current 1062 records)
        # rather than returning nothing.

    return vector_store.similarity_search(question, k=k)


if __name__ == "__main__":
    # Quick manual check, same spirit as query_test.py but exercising the
    # actual function other code will call — not a separate code path.
    if len(sys.argv) < 2:
        print('Usage: python scripts/retriever.py "your question"')
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    results = retrieve(question)

    print(f'\nRetrieved {len(results)} document(s) for: "{question}"\n')
    for doc in results:
        print(f"[{doc.metadata.get('cve_id')}] {doc.page_content[:150]}...")
        print()