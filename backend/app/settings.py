from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    database_sync_url: str = ""  # required for migrations/tests only, not at runtime
    app_env: str = "development"  # "development" | "production"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
