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
    deepseek_api_key: str = ""
    ai_daily_budget_usd: float = 5.0
    ai_timeout_seconds: int = 15
    ai_retry_count: int = 2
    ai_retry_backoff_seconds: float = 0.35
    ai_default_providers: str = "claude,gpt5,grok,deepseek"
    ai_provider_weights: str = "claude=1.0,gpt5=1.0,grok=1.0,deepseek=1.0"
    claude_model: str = "claude-opus-4-6"
    gpt_model: str = "gpt-5.2"
    grok_model: str = "grok-4.1-fast"
    deepseek_model: str = "deepseek-chat"
    jwt_secret: str = "change_me"
    jwt_expire_minutes: int = 60
    api_daily_limit: int = 200
    quote_short_cache_ttl_seconds: int = 5
    quote_fetch_rate_limit: int = 20
    quote_fetch_rate_window_seconds: int = 10
    cors_allow_origins: str = "https://stockmai-frontend.onrender.com,http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

