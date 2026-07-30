from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI AP & GL Copilot"
    database_url: str = "sqlite:///./backend/demo.db"
    markdown_repository_path: str = "knowledge-vault"
    enable_openai_embeddings: bool = False
    max_result_rows: int = 500
    query_timeout_seconds: int = 10

    model_config = SettingsConfigDict(env_file=".env.local", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
