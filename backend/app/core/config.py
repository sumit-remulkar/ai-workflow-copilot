from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ai-workflow-copilot"
    app_env: str = "local"
    app_debug: bool = True

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/copilot"
    redis_url: str = "redis://localhost:6379/0"
    upload_dir: str = "./data/uploads"

    llm_provider: str = "auto"  # auto | openai | azure | mock
    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-10-21"
    azure_openai_deployment: str = "gpt-4o-mini"
    azure_openai_embedding_deployment: str = "text-embedding-3-small"

    embedding_dimension: int = 1536

    langfuse_secret_key: str = ""
    langfuse_public_key: str = ""
    langfuse_base_url: str = "https://cloud.langfuse.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
