from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.api.v1.api import api_router
from app.core.rate_limit import limiter
from app.core.config import settings
from app.services.telegram import telegram_service
import sys
import asyncio
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION
)

# --- Manejo de Errores Estándar ---

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Estandariza los errores de validación (422)."""
    errors = []
    for error in exc.errors():
        # Extraer el campo del error (ej: body -> email)
        field = error.get("loc")[-1] if error.get("loc") else "unknown"
        errors.append({
            "field": field,
            "message": error.get("msg"),
            "type": error.get("type")
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "code": "VALIDATION_ERROR",
            "message": "Error de validación en los datos enviados",
            "errors": errors
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Estandariza errores inesperados (500)."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Ha ocurrido un error interno en el servidor"
        }
    )

@app.on_event("startup")
async def startup_event():
    """Eventos al iniciar la aplicación."""
    if settings.TELEGRAM_ENABLED or settings.TELEGRAM_BOT_TOKEN:
        logger.info("Initializing Telegram Service...")
        asyncio.create_task(telegram_service.start())

@app.on_event("shutdown")
async def shutdown_event():
    """Eventos al cerrar la aplicación."""
    logger.info("Shutting down Telegram Service...")
    await telegram_service.stop()

# Configuración CSRF
class CsrfSettings(settings.__class__):
    authjwt_secret_key: str = settings.SECRET_KEY
    csrf_secret_key: str = settings.CSRF_SECRET_KEY
    csrf_cookie_samesite: str = "lax"

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()

@app.exception_handler(CsrfProtectError)
def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

# Middleware para Headers de Seguridad (Optimizado para evitar problemas de concurrencia)
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "img-src 'self' data: https://fastapi.tiangolo.com; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "connect-src 'self' ws://localhost:8000 ws://127.0.0.1:8000 http://localhost:3000 http://localhost:8000;"
    )
    return response

# app.add_middleware(SecurityHeadersMiddleware) # Reemplazado por @app.middleware

# Integrar Limiter a la app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configurar CORS (Seguridad: Orígenes restringidos desde settings)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
@limiter.limit(settings.RATE_LIMIT_HEALTH)
def health_check(request: Request):
    return {"status": "ok", "version": settings.PROJECT_VERSION}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
