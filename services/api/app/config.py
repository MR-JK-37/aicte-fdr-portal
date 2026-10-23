from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "dev"
    database_url: str = "postgresql+psycopg://fdr:fdr@localhost:5432/fdr"
    valkey_url: str = "redis://localhost:6379/0"
    garage_endpoint: str = "http://localhost:3900"
    garage_access_key: str = "devaccesskey"
    garage_secret_key: str = "devsecretkeydevsecretkey"
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "fdr-portal"


settings = Settings()
