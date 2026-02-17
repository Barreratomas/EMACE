from fastapi import APIRouter
from app.api.v1.endpoints import chat, inventory, auth, knowledge, iam, billing, telegram

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(iam.router, prefix="/iam", tags=["iam"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(telegram.router, tags=["telegram"])
