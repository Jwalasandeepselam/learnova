"""Application configuration settings for Learnova.

Loads environment variables from backend/.env and ensures required storage directories exist.
"""

from functools import lru_cache
import json
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime settings configured via environment variables."""

    # Server configuration
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Database & Storage
    DATABASE_URL: str = "sqlite:///./learnova.db"
    STORAGE_DIR: str = "./storage"
    CHROMA_PERSIST_DIR: str = "./storage/chroma_db"

    # AI Model Providers
    DEFAULT_LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    LOCAL_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Union[str, List[str]]) -> List[str]:
        """Parse JSON or comma-separated string representation of CORS_ORIGINS."""
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return [str(origin).strip() for origin in parsed]
                except json.JSONDecodeError:
                    pass
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def storage_path(self) -> Path:
        """Absolute or relative Path object for STORAGE_DIR."""
        return Path(self.STORAGE_DIR).resolve()

    @property
    def uploads_dir(self) -> Path:
        """Path for raw uploaded files."""
        return self.storage_path / "uploads"

    @property
    def study_packs_dir(self) -> Path:
        """Path for generated study packs (PDFs and JSON)."""
        return self.storage_path / "study_packs"

    @property
    def chroma_dir(self) -> Path:
        """Path for Chroma vector database storage."""
        return Path(self.CHROMA_PERSIST_DIR).resolve()

    def ensure_directories(self) -> None:
        """Ensure all required local storage directories exist."""
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.study_packs_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Retrieve cached application settings instance and ensure directory tree."""
    app_settings = Settings()
    app_settings.ensure_directories()
    return app_settings


# Global settings singleton
settings = get_settings()
