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
import sys
import asyncio
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from app.core.security import decode_token
from app.core.database.session import engine
from sqlmodel import Session, select
from app.core.database.models import VendorAccessState, User, VendorMtprotoSession
from datetime import datetime, timezone
from sqlmodel import select
from app.core.telegram_mtproto import mtproto_manager
from app.core.checkpoint import get_postgres_checkpointer
from app.graph.workflow import workflow as graph
from langchain_core.messages import HumanMessage, AIMessage
from app.core.database.session import get_async_sessionmaker
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import httpx
from app.core.security import decrypt_secret
from app.repositories.telegram_integration import telegram_integration_repo

def _setup_logging():
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)
    log_dir = settings.LOG_DIR
    log_file = settings.LOG_FILE
    os.makedirs(log_dir, exist_ok=True)
    filepath = os.path.join(log_dir, log_file)
    handler = TimedRotatingFileHandler(
        filename=filepath,
        when=settings.LOG_ROTATE_WHEN,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding="utf-8",
        utc=False,
    )
    if settings.LOG_JSON:
        fmt = '{"ts":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","pid":%(process)d,"thread":"%(threadName)s","msg":%(message)s}'
    else:
        fmt = "%(asctime)s %(levelname)s %(name)s %(process)d %(threadName)s %(message)s"
    formatter = logging.Formatter(fmt=fmt, datefmt="%Y-%m-%dT%H:%M:%S%z")
    handler.setFormatter(formatter)
    root.addHandler(handler)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        lg.setLevel(level)
        lg.addHandler(handler)

_setup_logging()

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
    # Registro dinámico de webhooks de Telegram si hay URL pública efectiva
    base_url = settings.EFFECTIVE_TELEGRAM_PUBLIC_BASE_URL
    if base_url:
        logger.info({"event": "startup.telegram.sync_webhooks", "base_url": base_url})
        async_session = get_async_sessionmaker()
        async with async_session() as session:
            active_integrations = await telegram_integration_repo.get_all_active(session)
            async with httpx.AsyncClient(timeout=10) as client:
                for integration in active_integrations:
                    try:
                        token = decrypt_secret(integration.bot_token_encrypted)
                        webhook_url = f"{base_url}{settings.API_V1_STR}/telegram/webhook/{integration.vendor_id}/{integration.webhook_secret}"
                        resp = await client.post(
                            f"https://api.telegram.org/bot{token}/setWebhook",
                            json={"url": webhook_url}
                        )
                        if resp.status_code == 200:
                            logger.info({
                                "event": "startup.telegram.webhook_synced",
                                "vendor_id": integration.vendor_id,
                                "bot": integration.bot_username
                            })
                        else:
                            logger.warning({
                                "event": "startup.telegram.webhook_sync_failed",
                                "vendor_id": integration.vendor_id,
                                "status": resp.status_code,
                                "body": resp.text
                            })
                    except Exception as e:
                        logger.error({
                            "event": "startup.telegram.webhook_error",
                            "vendor_id": integration.vendor_id,
                            "error": str(e)
                        })

    # Observabilidad mínima para despliegue de MP
    if settings.MP_WEBHOOK_URL:
        logger.info({"event": "startup.mp.webhook_url", "url": settings.MP_WEBHOOK_URL, "endpoint": "/api/v1/billing/webhooks/mp"})
    else:
        logger.warning({"event": "startup.mp.webhook_url.missing", "endpoint": "/api/v1/billing/webhooks/mp"})
    # Iniciar daemon MTProto si está habilitado
    if settings.TELEGRAM_MTPROTO_ENABLED and not settings.TELEGRAM_MTPROTO_KILL_SWITCH:
        from app.core.botfather_orchestrator import botfather_orchestrator, BOTFATHER_ID

        async def mtproto_handler(vendor_id: int, text: str, meta: dict) -> None:
            chat_id = meta.get("chat_id")
            if not chat_id:
                return
            chat_username = str(meta.get("chat_username") or "").lower()
            is_botfather = str(chat_id) == str(BOTFATHER_ID) or chat_username == "botfather"
            if is_botfather:
                if botfather_orchestrator.has_active(vendor_id):
                    try:
                        await botfather_orchestrator.on_botfather_message(vendor_id, text, meta)
                    except Exception as e:
                        logger.error(
                            {
                                "event": "mtproto.botfather.handler.error",
                                "vendor_id": vendor_id,
                                "error": str(e)[:200],
                            }
                        )
                return
            logger.info(
                {
                    "event": "mtproto.message.ignored_non_botfather",
                    "vendor_id": vendor_id,
                    "chat_id": str(chat_id),
                    "chat_username": chat_username or None,
                }
            )

        mtproto_manager.set_handler(mtproto_handler)
        stop = False
        async def mtproto_loop():
            nonlocal stop
            async_session = get_async_sessionmaker()
            while not stop:
                try:
                    async with async_session() as db:
                        result = await db.execute(select(VendorMtprotoSession).where(VendorMtprotoSession.enabled == True))
                        rows = result.scalars().all()
                        for rec in rows:
                            await mtproto_manager.ensure_connected(rec.vendor_id)
                except Exception as e:
                    logger.warning({"event": "mtproto.loop.error", "error": str(e)[:200]})
                await asyncio.sleep(20)
        app.state.mtproto_stop_flag = lambda: setattr(sys.modules[__name__], "stop", True)
        app.state.mtproto_task = asyncio.create_task(mtproto_loop())

@app.on_event("shutdown")
async def shutdown_event():
    """Eventos al cerrar la aplicación."""
    logger.info("Shutting down application...")
    # Apagar daemon MTProto si estaba en ejecución
    task = getattr(app.state, "mtproto_task", None)
    if task:
        task.cancel()
        try:
            await task
        except Exception:
            pass
    try:
        await mtproto_manager.shutdown()
    except Exception:
        pass

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
    # Cargar contexto de acceso del vendor (best-effort, no bloqueante)
    try:
        auth = request.headers.get("Authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1]
            payload = decode_token(token)
            sub = payload.get("sub")
            if sub:
                with Session(engine) as db:
                    user = db.exec(select(User).where(User.id == int(sub))).first()
                    if user:
                        vendor_id = user.parent_id if user.parent_id is not None else user.id
                        state = db.exec(select(VendorAccessState).where(VendorAccessState.vendor_id == vendor_id)).first()
                        if state:
                            now = datetime.now(timezone.utc)
                            valid = True
                            if state.access_mode == "lifetime":
                                valid = True
                            elif state.valid_until:
                                valid = state.valid_until > now
                            else:
                                valid = False
                            request.state.vendor_access = {
                                "vendor_id": vendor_id,
                                "access_mode": state.access_mode,
                                "source": state.source,
                                "valid_until": state.valid_until,
                                "valid": valid
                            }
    except Exception:
        # Silencioso para no bloquear la request si algo falla
        pass
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


@app.get("/metrics")
async def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
