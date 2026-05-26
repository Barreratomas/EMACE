from logging import WARNING
from typing import List, Union
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator

class Settings(BaseSettings):
    # API Info
    PROJECT_NAME: str = "Agent Ecosystem API"
    PROJECT_DESCRIPTION: str = "API Profesional para el Ecosistema de Agentes Cognitivos"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"


    # cada nivel de logging es un umbral donde todo lo que está por debajo de ese umbral no se registra.
    # - CRITICAL (50) — usar cuando el sistema queda inutilizable o hay riesgo de corrupción de datos; caída al iniciar, pérdida de conexión crítica persistente.
    # - ERROR (40) — fallas que impactan la operación de una request o tarea; excepciones no recuperadas, errores de DB, setWebhook fallido.
    # - WARNING (30) — condiciones inesperadas pero recuperables; timeouts transitorios, reintentos, datos incompletos no fatales.
    # - INFO (20) — flujo normal del sistema; inicio, ruteos del supervisor, operaciones exitosas clave, métricas importantes.
    # - DEBUG (10) — detalle fino para desarrollo; payloads resumidos, tiempos de cada paso, decisiones del agente. Evitar en producción salvo troubleshooting.
    # - NOTSET (0) — no recomendable; hereda del logger padre y puede generar comportamientos ambiguos.
    # Logging
    LOG_LEVEL: str = "INFO" 
    LOG_DIR: str = "logs"
    LOG_FILE: str = "app.log"
    LOG_ROTATE_WHEN: str = "midnight"
    LOG_BACKUP_COUNT: int = 14
    LOG_JSON: bool = False

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000", # Frontend Next.js
        "http://localhost:8081", # Adminer
        "http://localhost:8000", # Self / Docs
        "http://127.0.0.1:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    import json
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return v

    # Database
    DATABASE_URL: str
    
    # Redis (Background Jobs)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 15
    KNOWLEDGE_MAX_MB_PER_VENDOR: int = 50
    CSRF_SECRET_KEY: str 
    
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
    TELEGRAM_MTPROTO_ENABLED: bool = False
    TELEGRAM_MTPROTO_KILL_SWITCH: bool = False
    TELEGRAM_MTPROTO_ALLOWED_VENDORS: str | None = None
    TELEGRAM_MTPROTO_API_ID: int | None = None
    TELEGRAM_MTPROTO_API_HASH: str | None = None
    TELEGRAM_PUBLIC_BASE_URL: str | None = None

    # Mercado Pago
    MP_ACCESS_TOKEN: str | None = None
    MP_WEBHOOK_SECRET: str | None = None
    MP_WEBHOOK_URL: str | None = None
    MP_CURRENCY_ID: str = "ARS"

    @property
    def EFFECTIVE_TELEGRAM_PUBLIC_BASE_URL(self) -> str | None:
        """
        Calcula la URL pública efectiva para Telegram.
        Si TELEGRAM_PUBLIC_BASE_URL está definido, se usa ese.
        Si no, intenta deducirla de MP_WEBHOOK_URL (que suele ser el túnel de Cloudflare).
        """
        if self.TELEGRAM_PUBLIC_BASE_URL:
            return str(self.TELEGRAM_PUBLIC_BASE_URL).rstrip("/")
        
        if self.MP_WEBHOOK_URL:
            # MP_WEBHOOK_URL suele ser algo como https://dominio.trycloudflare.com/api/v1/billing/webhook/mp
            # Queremos extraer solo el esquema y el host: https://dominio.trycloudflare.com
            from urllib.parse import urlparse
            parsed = urlparse(self.MP_WEBHOOK_URL)
            if parsed.scheme and parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}"
        
        return None

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
