from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    model_path: Path = Path("ml/artifacts/model/salary_model.joblib")
    model_metadata_path: Path = Path("ml/artifacts/model/model_metadata.json")
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    cors_allowed_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


settings = Settings()
