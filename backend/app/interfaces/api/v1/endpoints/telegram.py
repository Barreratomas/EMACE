from typing import Any, Dict
import logging
from fastapi import APIRouter, Depends, status, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_async_session
from app.infrastructure.repositories.telegram_integration import telegram_integration_repo
from app.infrastructure.repositories.auth import AuthRepository
from app.infrastructure.repositories.audit import audit_repo
from app.infrastructure.adapters.rate_limit import limiter, telegram_webhook_key
from app.application.use_cases.telegram_use_cases import TelegramUseCases

from app.interfaces.api.deps import get_current_user, get_tenant_owner_id, get_background_job_port
from app.domain.models import User
from app.domain.ports.background_jobs import IBackgroundJobPort

router = APIRouter()
logger = logging.getLogger(__name__)

auth_repo = AuthRepository()

def get_telegram_use_cases(
    background_job_port: IBackgroundJobPort = Depends(get_background_job_port)
) -> TelegramUseCases:
    return TelegramUseCases(
        telegram_repo=telegram_integration_repo, 
        auth_repo=auth_repo,
        audit_repo=audit_repo,
        background_job_port=background_job_port
    )

@router.get("/vendors/me/integrations/telegram/status")
async def get_telegram_status(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    use_cases: TelegramUseCases = Depends(get_telegram_use_cases),
):
    """Obtiene el estado de la integración del bot de Telegram (webhook)"""
    tenant_id = get_tenant_owner_id(current_user)
    return await use_cases.get_status(session, tenant_id)


@router.get("/vendors/me/integrations/telegram/mtproto/status")
async def get_telegram_mtproto_status(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    use_cases: TelegramUseCases = Depends(get_telegram_use_cases),
):
    """Obtiene el estado de la conexión MTProto (BotFather/User session)"""
    tenant_id = get_tenant_owner_id(current_user)
    return await use_cases.get_mtproto_status(session, tenant_id)


@router.post("/telegram/webhook/{vendor_public_id}/{webhook_secret}")
@limiter.limit("60/minute", key_func=telegram_webhook_key)
async def telegram_webhook(
    vendor_public_id: str,
    webhook_secret: str,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    use_cases: TelegramUseCases = Depends(get_telegram_use_cases),
):
    """Recibe y procesa mensajes entrantes desde bots de Telegram integrados"""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_payload")

    return await use_cases.process_webhook(
        session, 
        vendor_public_id, 
        webhook_secret, 
        payload
    )
