from typing import List, Union
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, validator

class Settings(BaseSettings):
    # API Info
    PROJECT_NAME: str = "Agent Ecosystem API"
    PROJECT_DESCRIPTION: str = "API Profesional para el Ecosistema de Agentes Cognitivos"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000", # Frontend Next.js
        "http://localhost:8081", # Adminer
        "http://localhost:8000", # Self / Docs
        "http://127.0.0.1:3000",
    ]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CSRF_SECRET_KEY: str = "csrf-secret-key-change-in-production"
    
    # Rate Limiting
    RATE_LIMIT_HEALTH: str = "10/minute"
    RATE_LIMIT_READ_PRODUCTS: str = "60/minute"
    RATE_LIMIT_WRITE_PRODUCTS: str = "10/minute"
    RATE_LIMIT_UPDATE_PRODUCTS: str = "20/minute"
    RATE_LIMIT_DELETE_PRODUCTS: str = "5/minute"
    
    # Communications
    SMTP_ENABLED: bool = False
    SMTP_HOST: str | None = None
    SMTP_PORT: int | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None
    TELEGRAM_ENABLED: bool = False
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_DEFAULT_CHAT_ID: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Para retrocompatibilidad si es necesario, pero idealmente usar get_settings()
settings = get_settings()
