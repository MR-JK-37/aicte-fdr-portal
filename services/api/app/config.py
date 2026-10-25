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
    # Short-lived access token (AUTH_ROLES_MATRIX.md §2.1: "access token (<=15 min) in
    # memory, rotating refresh token ... bound to the device record"). Renamed from
    # the old jwt_expiration_seconds (was 86400s/24h with no refresh token at all).
    access_token_expiration_seconds: int = 900
    session_cookie_name: str = "fdr_session"
    refresh_cookie_name: str = "fdr_refresh"
    # AUTH_ROLES_MATRIX.md §2.2(9): "mobile refresh up to 30 days". Used as the
    # absolute session expiry for all clients this session — role-differentiated
    # idle/absolute timeouts (staff 15min/8h, institution 30min/12h, etc.) are not
    # implemented yet, tracked in docs/phase-reports/R2.md.
    refresh_token_expiration_days: int = 30
    # Local dev clients only: web dev server (:3000) and the mobile Expo *web*
    # preview target (:8082 — the only mobile target reachable in a sandbox with
    # no device/emulator). A packaged iOS/Android app is not a browser and is
    # never subject to CORS, so this list never needs to (and must not, for
    # anything beyond local dev) include a production mobile origin.
    cors_allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8082"]
    # Fernet key (32 url-safe base64 bytes) encrypting TOTP secrets at rest. The dev default is
    # a fixed, publicly-known key — fine for local/test, never for production. prod_guard should
    # eventually reject this default the same way it rejects the other known-dev-only settings
    # (tracked, not done this session).
    totp_encryption_key: str = "4u8x9h2mKpQw7vN3zT6bR1sL5cE0dY_fJaGiVoWnXkM="
    # AUTH_ROLES_MATRIX.md §2.2(8) defaults: lock after this many consecutive failures, for this
    # many minutes. Config, not a hard constant — override per-deployment via env.
    max_login_attempts: int = 10
    lockout_minutes: int = 15


settings = Settings()
