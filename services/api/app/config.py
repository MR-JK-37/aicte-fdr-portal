from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "dev"
    database_url: str = (
        "postgresql+psycopg://fdr_app:fdr_app_dev_password@localhost:5432/fdr"
    )
    # Used only by Alembic migrations, which must run as the table-owning
    # role to create the fdr_app runtime role, RLS policies and triggers.
    # The API/worker processes never use this.
    migration_database_url: str = "postgresql+psycopg://fdr:fdr@localhost:5432/fdr"
    valkey_url: str = "redis://localhost:6379/0"
    garage_endpoint: str = "http://localhost:3900"
    garage_access_key: str = "devaccesskey"
    garage_secret_key: str = "devsecretkeydevsecretkey"
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "fdr-portal"
    # Insight (text2sql) agent only — SELECT-only on an allow-listed view
    # set (app/agents/insight.py). Never used for anything else.
    readonly_database_url: str = (
        "postgresql+psycopg://fdr_readonly:fdr_readonly_dev_password@localhost:5432/fdr"
    )
    garage_bucket: str = "fdr-documents"
    # Mailpit in dev (real SMTP transaction, caught locally, never sent
    # out) — a real production SMTP relay is a deploy-time config swap,
    # not a code change (app/reminders/email.py just does smtplib.send).
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    production_telephony_enabled: bool = False
    clamav_host: str = "localhost"
    clamav_port: int = 3310
    jwt_secret: str = "dev-insecure-jwt-secret-for-signing-session-tokens-32bytes"
    jwt_algorithm: str = "HS256"
    jwt_expiration_seconds: int = 86400
    session_cookie_name: str = "fdr_session"


settings = Settings()
