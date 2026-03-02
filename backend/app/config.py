from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://twstock_user:twstock_pass@localhost:5432/twstock"
    redis_url: str = "redis://localhost:6379/0"

    # Optional keys for future modules
    finmind_token: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    grok_api_key: str = ""
    gemini_api_key: str = ""
    ai_timeout_seconds: int = 15
    ai_default_providers: str = "claude,gpt5,grok,gemini"
    jwt_secret: str = "change_me"
    jwt_expire_minutes: int = 60
    api_daily_limit: int = 200
    cors_allow_origins: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
