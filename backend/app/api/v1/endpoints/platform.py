from typing import List, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.config import settings
from app.core.rate_limit import limiter


router = APIRouter()


class PlatformFeatureFlag(BaseModel):
    key: str
    name: str
    enabled: bool
    status: str
    reason: Optional[str] = None


class PlatformFeaturesResponse(BaseModel):
    features: List[PlatformFeatureFlag]


@router.get("/features", response_model=PlatformFeaturesResponse)
@limiter.limit(settings.RATE_LIMIT_HEALTH)
async def get_platform_features(
    request: Request,
):
    features: List[PlatformFeatureFlag] = []

    billing_enabled = bool(settings.MP_ACCESS_TOKEN)
    billing_status = "ok" if billing_enabled else "disabled"
    billing_reason = None
    if not billing_enabled:
        billing_reason = "Integración de Mercado Pago no configurada"
    features.append(
        PlatformFeatureFlag(
            key="billing",
            name="Módulo de Facturación",
            enabled=billing_enabled,
            status=billing_status,
            reason=billing_reason,
        )
    )

    notifications_enabled = bool(settings.SMTP_ENABLED or settings.TELEGRAM_ENABLED)
    notifications_status = "ok" if notifications_enabled else "disabled"
    notifications_reason = None
    if not notifications_enabled:
        notifications_reason = "SMTP y Telegram desactivados"
    features.append(
        PlatformFeatureFlag(
            key="notifications",
            name="Notificaciones",
            enabled=notifications_enabled,
            status=notifications_status,
            reason=notifications_reason,
        )
    )

    integrations_enabled = bool(
        settings.TELEGRAM_ENABLED
        or settings.TELEGRAM_MTPROTO_ENABLED
        or settings.MP_ACCESS_TOKEN
    )
    integrations_status = "ok" if integrations_enabled else "partial"
    integrations_reason = None
    if not integrations_enabled:
        integrations_reason = "Sin integraciones externas configuradas"
    features.append(
        PlatformFeatureFlag(
            key="integrations",
            name="Integraciones externas",
            enabled=integrations_enabled,
            status=integrations_status,
            reason=integrations_reason,
        )
    )

    features.append(
        PlatformFeatureFlag(
            key="low_latency_api",
            name="API de baja latencia",
            enabled=True,
            status="ok",
            reason=None,
        )
    )
    features.append(
        PlatformFeatureFlag(
            key="encryption",
            name="Cifrado y seguridad",
            enabled=True,
            status="ok",
            reason=None,
        )
    )

    return PlatformFeaturesResponse(features=features)

