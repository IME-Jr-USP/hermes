from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Configurações que variam por ambiente (lidas de variáveis de ambiente ou .env)."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_prefix="HERMES_",
        extra="ignore",
    )

    # Agente
    agent_model: str = "google/gemini-3.6-flash"  # id do OpenRouter
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_api_key: SecretStr = SecretStr("")

    # Banco de Dados
    db_path: Path = BASE_DIR / "chroma_db"
    embedding_model: str = "BAAI/bge-m3"
    embedding_device: Literal["cpu", "cuda", "mps"] = "cpu"

    # API
    cors_origins: list[str] = ["http://localhost:5173"]

    # Logs
    log_dir: Path = BASE_DIR / "logs"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "DEBUG"

    @property
    def log_path(self) -> Path:
        return self.log_dir / "app.log"


settings = Settings()
