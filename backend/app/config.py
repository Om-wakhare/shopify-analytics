"""
Central configuration using Pydantic Settings.
All values are loaded from environment variables or .env file.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # ── App ──────────────────────────────────────────────────────────────
    APP_NAME: str = "Shopify Analytics Platform"
    DEBUG: bool = False
    SECRET_KEY: str  # used for session signing

    # ── Database ─────────────────────────────────────────────────────────
    # Railway injects DATABASE_URL as postgresql:// — we convert to asyncpg
    DATABASE_URL: str = "postgresql+asyncpg://localhost/railway"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    @property
    def async_database_url(self) -> str:
        """Always return asyncpg-compatible URL regardless of what Railway injects."""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    # ── Shopify OAuth ─────────────────────────────────────────────────────
    SHOPIFY_API_KEY: str
    SHOPIFY_API_SECRET: str
    SHOPIFY_API_VERSION: str = "2024-07"
    SHOPIFY_SCOPES: str = (
        "read_customers,read_orders,read_products,"
        "write_customers,write_orders"
    )
    # Base URL of THIS application (used to build redirect/webhook URLs)
    APP_BASE_URL: str  # e.g. https://yourapp.com

    # ── Redis / Celery ────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Webhook ───────────────────────────────────────────────────────────
    # Maximum number of retry attempts for failed webhook processing
    WEBHOOK_MAX_RETRIES: int = 5
    WEBHOOK_RETRY_BACKOFF: int = 60  # seconds base

    # ── Bulk Operations ───────────────────────────────────────────────────
    BULK_POLL_INTERVAL: int = 10   # seconds between status polls
    BULK_MAX_WAIT: int = 3600      # max seconds to wait for a bulk job

    # ── Frontend ──────────────────────────────────────────────────────────
    FRONTEND_URL: str = "https://shopify-analytics-igsp.vercel.app"

    # ── Currency ──────────────────────────────────────────────────────────
    DEFAULT_CURRENCY: str = "USD"


@lru_cache
def get_settings() -> Settings:
    return Settings()
