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

    # /narrate only: needs the cleaned dataset (comparison-group stats) and a
    # reachable narrator provider. /health, /model/info, /predict never touch
    # these. "ollama" (default) matches local dev where Ollama runs alongside
    # the API. "gemini" is for deployments (e.g. Render) that can't reach a
    # developer's local Ollama instance -- see backend/app/services/gemini_client.py.
    processed_dataset_path: Path = Path("ml/data/processed/salaries_clean.csv")
    narrator_provider: str = "ollama"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2:latest"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


settings = Settings()
