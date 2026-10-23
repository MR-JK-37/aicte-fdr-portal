from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "dev"
    database_url: str = "postgresql+psycopg://fdr_app:fdr_app_dev_password@localhost:5432/fdr"
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
    garage_bucket: str = "fdr-documents"
    clamav_host: str = "localhost"
    clamav_port: int = 3310


settings = Settings()
