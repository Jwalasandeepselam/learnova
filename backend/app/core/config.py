import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directories
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BACKEND_DIR.parent
ENV_FILE = BACKEND_DIR / ".env" if (BACKEND_DIR / ".env").exists() else ROOT_DIR / ".env"

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Database & Storage
    DATABASE_URL: str = "sqlite:///./learnova.db"
    STORAGE_DIR: str = str(ROOT_DIR / "storage")
    VECTOR_STORE_DIR: str = str(ROOT_DIR / "storage" / "vector_store")
    UPLOADS_DIR: str = str(ROOT_DIR / "storage" / "uploads")
    STUDY_PACKS_DIR: str = str(ROOT_DIR / "storage" / "study_packs")

    # LLM Providers
    DEFAULT_LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Embedding Providers
    AI_EMBEDDING_PROVIDER: str = "local"  # "gemini", "openai", "local"
    LOCAL_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def init_directories(self) -> None:
        """Ensure runtime storage directories exist."""
        for path_str in [self.STORAGE_DIR, self.VECTOR_STORE_DIR, self.UPLOADS_DIR, self.STUDY_PACKS_DIR]:
            p = Path(path_str)
            p.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.init_directories()
