"""Single configuration source. Paths resolve against the repository, not the shell."""
from functools import lru_cache
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    STORAGE_DIR: str = str(ROOT_DIR / "storage")
    LEARNING_DB_PATH: str = str(ROOT_DIR / "storage" / "learning.db")
    DATABASE_URL: str = "sqlite:///" + str(ROOT_DIR / "learnova.db").replace("\\", "/")
    VECTOR_STORE_DIR: str = str(ROOT_DIR / "storage" / "vector_store")
    CHROMA_PERSIST_DIR: str = str(ROOT_DIR / "storage" / "chroma_db")
    DEFAULT_LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    GEMINI_LIVE_MODEL: str = "gemini-3.8-live"
    AI_EMBEDDING_PROVIDER: str = "local"
    LOCAL_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    MAX_UPLOAD_MB: int = 20
    COOKIE_SECURE: bool = False
    SESSION_TTL_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=(str(ROOT_DIR / ".env"), str(BACKEND_DIR / ".env")),
        env_file_encoding="utf-8", extra="ignore",
    )

    @field_validator("STORAGE_DIR", "LEARNING_DB_PATH", "VECTOR_STORE_DIR", "CHROMA_PERSIST_DIR")
    @classmethod
    def absolute_path(cls, value: str) -> str:
        path = Path(value)
        return str(path if path.is_absolute() else (ROOT_DIR / path).resolve())

    @property
    def storage_path(self) -> Path:
        return Path(self.STORAGE_DIR)

    @property
    def uploads_dir(self) -> Path:
        return self.storage_path / "uploads"

    @property
    def study_packs_dir(self) -> Path:
        return self.storage_path / "study_packs"

    @property
    def chroma_dir(self) -> Path:
        return Path(self.CHROMA_PERSIST_DIR)

    @property
    def UPLOADS_DIR(self) -> str:
        return str(self.uploads_dir)

    @property
    def STUDY_PACKS_DIR(self) -> str:
        return str(self.study_packs_dir)

    def ensure_directories(self) -> None:
        for path in (self.uploads_dir, self.study_packs_dir, Path(self.VECTOR_STORE_DIR), Path(self.LEARNING_DB_PATH).parent):
            path.mkdir(parents=True, exist_ok=True)

    def init_directories(self) -> None:
        self.ensure_directories()


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
