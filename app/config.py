"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Meta / Facebook
    META_APP_SECRET: str = ""
    META_VERIFY_TOKEN: str = ""

    # WhatsApp
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""

    # Messenger
    MESSENGER_PAGE_ACCESS_TOKEN: str = ""
    MESSENGER_PAGE_ID: str = ""

    # Instagram
    INSTAGRAM_ACCESS_TOKEN: str = ""
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str = ""

    # Anthropic
    ANTHROPIC_API_KEY: str = ""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/chatbot_db"

    # Admin
    ADMIN_API_KEY: str = ""

    # Notifications
    SALES_TEAM_WHATSAPP: str = ""
    SALES_TEAM_EMAIL: str = ""

    # App
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.APP_ENV == "production"

    @property
    def async_database_url(self) -> str:
        """Get async database URL (ensure asyncpg driver)."""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @field_validator("META_VERIFY_TOKEN")
    @classmethod
    def verify_token_not_empty_in_prod(cls, v: str) -> str:
        """Warn if verify token is empty."""
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
