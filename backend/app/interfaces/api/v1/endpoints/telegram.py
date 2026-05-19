from typing import Any, Dict
import logging
from fastapi import APIRouter, Depends, status, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_async_session
from app.infrastructure.repositories.telegram_integration import telegram_integration_repo
from app.infrastructure.repositories.auth import AuthRepository
from app.infrastructure.adapters.rate_limit import limiter, telegram_webhook_key
from app.application.use_cases.telegram_use_cases import TelegramUseCases

router = APIRouter()
logger = logging.getLogger(__name__)

auth_repo = AuthRepository()
telegram_use_cases = TelegramUseCases(telegram_integration_repo, auth_repo)

@router.post("/telegram/webhook/{vendor_public_id}/{webhook_secret}")
@limiter.limit("60/minute", key_func=telegram_webhook_key)
async def telegram_webhook(
    vendor_public_id: str,
    webhook_secret: str,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """Recibe y procesa mensajes entrantes desde bots de Telegram integrados"""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_payload")

    return await telegram_use_cases.process_webhook(
        session, 
        vendor_public_id, 
        webhook_secret, 
        payload
    )
