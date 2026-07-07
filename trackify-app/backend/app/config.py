from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://user:pass@localhost/trackify"
    redis_url: str = "redis://localhost:6379"

    secret_key: str = "dev-only-secret-change-me"
    access_token_expire_minutes: int = 15
    refresh_token_expire_minutes: int = 10080  # 7 days

    tmdb_api_key: str = ""
    tmdb_bearer_token: str = ""
    rec_service_url: str = "http://localhost:8001"
    rec_service_key: str = ""


settings = Settings()
