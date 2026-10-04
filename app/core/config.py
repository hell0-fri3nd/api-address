from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./address_book.db"
    log_level: str = "INFO"
    rate_limit: str = "60/minute"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
