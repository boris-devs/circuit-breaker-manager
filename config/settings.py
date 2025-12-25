from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    TIMEOUT_CHECK_SERVICES: int = 15

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_DB_PORT: int = 5432
    POSTGRES_DB: str = "circuit_breaker_db"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
