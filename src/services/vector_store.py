from langchain_chroma import Chroma
from src.services.embedding import get_embedding_model
from src.core.config import settings

def get_vector_store():
    """Initializes and returns the Chroma vector store instance."""
    embedder = get_embedding_model()
    return Chroma(
        collection_name="nvd_cves",
        embedding_function=embedder,
        persist_directory=str(settings.chroma_db_dir)
    )
