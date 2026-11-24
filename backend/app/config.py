from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    asset_storage_dir: str = "./storage/assets"
    database_path: str = "./storage/polygen_jobs.db"
    job_timeout_seconds: int = 120
    max_asset_size_mb: int = 50
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
    ai_provider_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def storage_path(self) -> Path:
        root = Path(__file__).resolve().parents[2]
        configured = Path(self.asset_storage_dir)
        path = configured if configured.is_absolute() else (root / configured).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def db_file_path(self) -> Path:
        root = Path(__file__).resolve().parents[2]
        configured = Path(self.database_path)
        path = configured if configured.is_absolute() else (root / configured).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def allowed_origins(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def max_asset_size_bytes(self) -> int:
        return self.max_asset_size_mb * 1024 * 1024


settings = Settings()