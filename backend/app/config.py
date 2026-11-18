from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    asset_storage_dir: str = "./storage/assets"
    job_timeout_seconds: int = 120
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


settings = Settings()