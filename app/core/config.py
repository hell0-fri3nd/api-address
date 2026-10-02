from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    
    project_name: str = "API Address Book"
    api_prefix: str = "/api/v1"
    database_uri: str = "sqlite:///./api_address.db"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
config = Config()