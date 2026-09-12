import json
import sys
from pathlib import Path
from langchain_core.documents import Document
from rich.console import Console
from rich.progress import track

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.core.config import settings
from src.services.vector_store import get_vector_store

console = Console()

def process_and_index_cves():
    raw_path = settings.raw_data_dir / "cves_raw.json"
    
    if not raw_path.exists():
        console.print("[red]Error: cves_raw.json not found. Run fetch_cves.py first.[/red]")
        return

    with open(raw_path, "r", encoding="utf-8") as f:
        raw_cves = json.load(f)

    documents = []
    for item in track(raw_cves, description="Processing CVEs..."):
        cve_data = item.get("cve", {})
        cve_id = cve_data.get("id")
        
        if not cve_id:
            continue

        descriptions = cve_data.get("descriptions", [])
        en_desc = next((d.get("value") for d in descriptions if d.get("lang") == "en"), "")
        
        if not en_desc:
            continue

        weaknesses = cve_data.get("weaknesses", [])
        cwe_id = "N/A"
        if weaknesses and weaknesses[0].get("description"):
            cwe_id = weaknesses[0]["description"][0].get("value", "N/A")

        metrics = cve_data.get("metrics", {}).get("cvssMetricV31", [])
        base_score = metrics[0]["cvssData"]["baseScore"] if metrics else 0.0

        metadata = {
            "cve_id": cve_id,
            "cwe": cwe_id,
            "cvss_score": float(base_score)
        }
        
        doc = Document(page_content=en_desc, metadata=metadata)
        documents.append(doc)

    console.print(f"[bold blue]Parsed {len(documents)} documents. Initializing vector store...[/bold blue]")
    vector_store = get_vector_store()
    
    console.print("[bold blue]Generating local embeddings and inserting into ChromaDB...[/bold blue]")
    
    # NEW IMPLEMENTATION HERE
    ids = [doc.metadata["cve_id"] for doc in documents]
    vector_store.add_documents(documents, ids=ids)
    
    console.print(f"[bold green]Successfully indexed {len(documents)} CVEs into ChromaDB![/bold green]")

if __name__ == "__main__":
    process_and_index_cves()