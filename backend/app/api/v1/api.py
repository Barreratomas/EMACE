from fastapi import APIRouter
from app.api.v1.endpoints import chat, inventory, auth, knowledge, iam, billing, telegram

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(
    inventory.dashboard_router,
    prefix="/vendors/me/dashboard",
    tags=["dashboard"],
)
api_router.include_router(
    inventory.agents_router,
    prefix="/vendors/me",
    tags=["agents"],
)
api_router.include_router(
    inventory.analytics_router,
    prefix="/vendors/me",
    tags=["analytics"],
)
api_router.include_router(
    inventory.platform_router,
    prefix="/platform",
    tags=["platform"],
)
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(iam.router, prefix="/iam", tags=["iam"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(telegram.router, tags=["telegram"])
