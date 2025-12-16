from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# its an relative path finding for base dirctory
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    """The below Configurations will be loaded from environment variables and also .env.dev."""
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env.dev", 
        env_file_encoding='utf-8'
    )
    
    # Redis configurations
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # Rate Limiter Parameters
    WINDOW_DURATION_SECONDS: int = 3600
    TTL_BUFFER_SECONDS: int = 60
    DEFAULT_MAX_REQUESTS: int = 100
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
settings = Settings()