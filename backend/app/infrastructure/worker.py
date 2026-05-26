import asyncio
import logging
import os
import httpx
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from arq.connections import RedisSettings
from langchain_core.messages import HumanMessage, AIMessage

from app.infrastructure.config import Settings
from app.infrastructure.database.session import get_async_sessionmaker
from app.infrastructure.adapters.checkpoint import get_postgres_checkpointer
from app.application.graph.workflow import workflow_builder as graph
from app.infrastructure.security import decrypt_secret
from app.domain.models import Customer, AuditLog
from app.infrastructure.repositories.auth import AuthRepository
from app.infrastructure.repositories.telegram_integration import telegram_integration_repo
from app.infrastructure.adapters.rag.ingestion import IngestionService
from app.infrastructure.adapters.comm.notifications import _send_email, _render_template, _extract_kv

logger = logging.getLogger(__name__)
auth_repo = AuthRepository()
ingestion_service = IngestionService()

# Cargar configuraciones
settings = Settings()

async def startup(ctx: Dict[Any, Any]):
    """
    Se ejecuta al iniciar el worker. 
    Aquí se pueden inicializar conexiones a DB, clientes de LLM, etc.
    """
    print("Iniciando Worker de EMACE...")
    ctx['sessionmaker'] = get_async_sessionmaker()
    ctx['http_client'] = httpx.AsyncClient(timeout=10)
    pass

async def shutdown(ctx: Dict[Any, Any]):
    """
    Se ejecuta al cerrar el worker.
    """
    print("Cerrando Worker de EMACE...")
    if 'http_client' in ctx:
        await ctx['http_client'].aclose()
    pass

# --- Registro de Tareas ---

async def test_task(ctx: Dict[Any, Any], name: str):
    """Tarea de prueba para verificar que el worker funciona"""
    print(f"Ejecutando tarea de prueba para: {name}")
    await asyncio.sleep(2)
    print(f"Tarea de prueba completada para: {name}")
    return f"Hola {name}, la tarea funcionó!"

async def process_telegram_message_task(
    ctx: Dict[Any, Any], 
    vendor_id: int, 
    chat_id: str, 
    text: str, 
    customer_id: Optional[int] = None
):
    """
    Procesa un mensaje de Telegram usando LangGraph y envía la respuesta.
    """
    sessionmaker = ctx['sessionmaker']
    http_client = ctx['http_client']
    
    start = time.monotonic()
    success = False
    reply_text: Optional[str] = None

    async with sessionmaker() as session:
        # Obtener integración para el token
        integration = await telegram_integration_repo.get_by_vendor_id(session, vendor_id)
        if not integration:
            logger.error(f"No integration found for vendor {vendor_id} in background task")
            return

        async with get_postgres_checkpointer() as checkpointer:
            app = graph.compile(checkpointer=checkpointer)
            config = {
                "configurable": {
                    "thread_id": f"telegram_{chat_id}",
                    "user_id": vendor_id,
                    "customer_id": customer_id,
                    "channel": "telegram_vendor_bot",
                    "user_role": "customer",
                    "user_permissions": ["customer:access"],
                }
            }
            try:
                result = await app.ainvoke({"messages": [HumanMessage(content=text)]}, config)
                msgs = result.get("messages", []) if isinstance(result, dict) else []
                for m in reversed(msgs):
                    if isinstance(m, AIMessage) and m.content:
                        if "QA Notification" not in str(m.content):
                            reply_text = str(m.content)
                            break
                success = True
            except Exception as e:
                logger.exception({"event": "telegram.worker.error", "vendor_id": vendor_id, "chat_id": chat_id})
                integration.last_error = str(e)[:500]
                session.add(integration)
                await session.commit()

        duration_ms = int((time.monotonic() - start) * 1000)
        
        # Registrar métrica de auditoría
        metric = AuditLog(
            user_id=vendor_id,
            agent_name="TelegramWorker",
            action="telegram_worker_metric",
            details=f"vendor_id={vendor_id}|chat_id={chat_id}|success={success}|duration_ms={duration_ms}",
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        session.add(metric)
        await session.commit()

        # Enviar respuesta al usuario vía API de Telegram
        if reply_text:
            try:
                token = decrypt_secret(integration.bot_token_encrypted)
                if token:
                    await http_client.post(
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        json={"chat_id": chat_id, "text": reply_text},
                    )
            except Exception as e:
                logger.error(f"Error sending telegram response from worker: {e}")

    return {"ok": success}

async def ingest_document_task(
    ctx: Dict[Any, Any], 
    file_path: str, 
    user_id: int
):
    """
    Tarea para procesar la ingesta de un documento en RAG de forma asíncrona.
    """
    logger.info(f"Iniciando ingesta de documento: {file_path} para usuario {user_id}")
    try:
        # IngestionService ya maneja la lógica de carga, splitting y upsert
        ingestion_service.ingest_file(file_path, user_id=user_id)
        logger.info(f"Ingesta completada exitosamente: {file_path}")
        return {"status": "completed", "file_path": file_path}
    except Exception as e:
        logger.error(f"Error en ingesta de documento {file_path}: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}
    finally:
        # Limpiar archivo temporal después de procesar
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Archivo temporal eliminado: {file_path}")
            except Exception as e:
                logger.error(f"No se pudo eliminar archivo temporal {file_path}: {e}")

async def send_notification_task(
    ctx: Dict[Any, Any],
    user_id: int,
    action: str,
    details: str
):
    """
    Procesa y envía notificaciones (Email/Telegram) basadas en eventos de auditoría.
    """
    sessionmaker = ctx['sessionmaker']
    http_client = ctx['http_client']
    
    # Extraer datos de los detalles (usando la lógica de notifications.py)
    payload = {}
    if action == "low_stock_alert":
        payload = {
            "name": _extract_kv(details, "name") or "Desconocido",
            "stock": _extract_kv(details, "stock") or "0",
            "threshold": _extract_kv(details, "threshold") or "0"
        }
    elif action == "invoice_due_soon":
        payload = {
            "invoice_id": _extract_kv(details, "invoice_id") or "N/A",
            "amount": _extract_kv(details, "amount") or "0",
            "due_date": _extract_kv(details, "due_date") or "N/A"
        }
    elif action == "appointment_upcoming":
        payload = {
            "role": _extract_kv(details, "role") or "Agente",
            "datetime": _extract_kv(details, "datetime") or "N/A"
        }

    subject, body = _render_template(action, payload)

    async with sessionmaker() as session:
        # 1. Intentar enviar por Email
        user = await auth_repo.get_user_by_id(session, user_id)
        if user and user.email:
            # _send_email es actualmente síncrona en notifications.py, pero la llamamos desde aquí
            success, msg = _send_email([user.email], subject, body)
            if success:
                logger.info(f"Email enviado a {user.email} para acción {action}")
            else:
                logger.warning(f"Fallo envío de email a {user.email}: {msg}")

        # 2. Intentar enviar por Telegram si el vendor tiene integración
        integration = await telegram_integration_repo.get_by_vendor_id(session, user_id)
        if integration and integration.is_active and integration.bot_token_encrypted:
            try:
                token = decrypt_secret(integration.bot_token_encrypted)
                if token:
                    # Usar el chat_id del primer admin o un chat configurado por defecto
                    # Por simplicidad, aquí se asume que el sistema sabe a quién notificar
                    # En una implementación real, buscaríamos el chat_id del vendor/admin
                    pass 
            except Exception as e:
                logger.error(f"Error enviando notificación por Telegram: {e}")

    return {"ok": True}

async def run_vendor_checks_task(ctx: Dict[Any, Any], vendor_id: int):
    """
    Ejecuta todos los chequeos proactivos para un vendor específico.
    """
    from app.infrastructure.adapters.scheduler import (
        _check_low_stock, _check_zero_stock_auto_pause, 
        _check_invoice_due, _check_appointments, _check_trial_expiration
    )
    
    sessionmaker = ctx['sessionmaker']
    async with sessionmaker() as session:
        # Nota: Los chequeos del scheduler actual usan Session síncrona de SQLModel
        # Para compatibilidad con el worker async, necesitamos pasar la sesión correctamente
        # o refactorizar los chequeos a async. Por ahora, los envolvemos.
        
        # Obtener el objeto User de la sesión
        user = await auth_repo.get_user_by_id(session, vendor_id)
        if not user:
            return
            
        # Ejecutar chequeos (esto generará AuditLogs que luego dispararán notificaciones)
        # TODO: Refactorizar estos métodos a async para evitar bloqueos
        # Por ahora los llamamos usando run_in_executor o simplemente asumiendo que son rápidos
        from sqlmodel import Session
        from app.infrastructure.database.session import engine
        with Session(engine) as sync_session:
            sync_user = sync_session.get(User, vendor_id)
            if sync_user:
                _check_low_stock(sync_session, sync_user)
                _check_zero_stock_auto_pause(sync_session, sync_user)
                _check_invoice_due(sync_session, sync_user)
                _check_appointments(sync_session, sync_user)
                _check_trial_expiration(sync_session, sync_user)
                sync_session.commit()
    
    return {"ok": True, "vendor_id": vendor_id}

# --- Configuración del Worker ---

class WorkerSettings:
    """
    Configuración que lee el comando 'arq app.infrastructure.worker.WorkerSettings'
    """
    functions = [
        test_task, 
        process_telegram_message_task, 
        ingest_document_task,
        send_notification_task,
        run_vendor_checks_task
    ]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    on_startup = startup
    on_shutdown = shutdown
    
    # Opcional: Configuración de reintentos por defecto
    max_retries = 3
    retry_delay = 5  # segundos
