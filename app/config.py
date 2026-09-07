"""Application settings loaded from environment variables."""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    log_level: str = "INFO"

    # Email settings (Resend)
    resend_api_key: Optional[str] = None
    email_from: str = "Summit Air <onboarding@resend.dev>"
    email_enabled: bool = True
    admin_notification_email: str = "axeldelakowski@gmail.com"


settings = Settings()
