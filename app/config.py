"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    log_level: str = "INFO"
    webhook_base_url: str = ""

    # Technician schedule DB (SQLite). Empty → in-memory (tests).
    # Cloud Run: use a mounted volume path or /tmp for single-instance demos.
    schedule_db_path: str = "data/schedule.db"

    # Post-call email summary
    summary_email_to: str = ""
    summary_email_from: str = "Summit Air Alex <onboarding@resend.dev>"
    resend_api_key: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True

    # Optional: verify Retell event webhooks (skipped if empty)
    retell_api_key: str = ""


settings = Settings()
