from fastapi import APIRouter
from app.api.v1.endpoints import (
    agents,
    analytics,
    auth,
    billing,
    chat,
    dashboard,
    inventory,
    knowledge,
    iam,
    platform,
    telegram,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(
    dashboard.router,
    prefix="/vendors/me/dashboard",
    tags=["dashboard"],
)
api_router.include_router(
    agents.router,
    prefix="/vendors/me",
    tags=["agents"],
)
api_router.include_router(
    analytics.router,
    prefix="/vendors/me",
    tags=["analytics"],
)
api_router.include_router(
    platform.router,
    prefix="/platform",
    tags=["platform"],
)
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(iam.router, prefix="/iam", tags=["iam"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(telegram.router, tags=["telegram"])
