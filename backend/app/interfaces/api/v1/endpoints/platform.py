from fastapi import APIRouter, Request
from app.infrastructure.adapters.rate_limit import limiter
from app.infrastructure.config import settings
from app.application.use_cases.platform_use_cases import PlatformUseCases, PlatformFeaturesResponse

router = APIRouter()
platform_use_cases = PlatformUseCases()

@router.get("/features", response_model=PlatformFeaturesResponse)
@limiter.limit(settings.RATE_LIMIT_HEALTH)
async def get_platform_features(
    request: Request,
):
    """Consulta la disponibilidad y estado de las funcionalidades globales de la plataforma"""
    return await platform_use_cases.get_features()
