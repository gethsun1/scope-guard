from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "development"
    demo_mode: bool = True
    database_url: str = "sqlite+aiosqlite:///./scopeguard.db"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.6"
    codex_provider: str = "demo"
    codex_app_server_url: str | None = None
    allowed_origins: str = "http://localhost:3000"
    audit_signing_secret: str = "local-demo-only"
    demo_workspace_root: str = "/workspace"
    demo_runner_url: str = "http://runner:9000"
    demo_api_token: str = "scope-guard-demo"
    log_level: str = "INFO"


@lru_cache
def settings() -> Settings:
    return Settings()

