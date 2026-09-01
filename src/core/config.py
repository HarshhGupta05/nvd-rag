from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    nvd_api_key: str = ""
    openai_api_key: str = ""
    
    project_root: Path = Path(__file__).resolve().parent.parent.parent
    raw_data_dir: Path = project_root / "data" / "raw"
    chroma_db_dir: Path = project_root / "chroma_db"
    
    top_k_retrieval: int = 5
    embedding_model: str = "all-MiniLM-L6-v2"
    llm_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()