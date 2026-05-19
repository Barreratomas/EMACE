from typing import List, Optional
from pydantic import BaseModel
from app.infrastructure.config import settings

class PlatformFeatureFlag(BaseModel):
    key: str
    name: str
    enabled: bool
    status: str
    reason: Optional[str] = None

class PlatformFeaturesResponse(BaseModel):
    features: List[PlatformFeatureFlag]

class PlatformUseCases:
    async def get_features(self) -> PlatformFeaturesResponse:
        features: List[PlatformFeatureFlag] = []

        # Billing
        billing_enabled = bool(settings.MP_ACCESS_TOKEN)
        features.append(
            PlatformFeatureFlag(
                key="billing",
                name="Módulo de Facturación",
                enabled=billing_enabled,
                status="ok" if billing_enabled else "disabled",
                reason=None if billing_enabled else "Integración de Mercado Pago no configurada",
            )
        )

        # Notifications
        notifications_enabled = bool(settings.SMTP_ENABLED or settings.TELEGRAM_ENABLED)
        features.append(
            PlatformFeatureFlag(
                key="notifications",
                name="Notificaciones",
                enabled=notifications_enabled,
                status="ok" if notifications_enabled else "disabled",
                reason=None if notifications_enabled else "SMTP y Telegram desactivados",
            )
        )

        # Integrations
        integrations_enabled = bool(
            settings.TELEGRAM_ENABLED
            or settings.TELEGRAM_MTPROTO_ENABLED
            or settings.MP_ACCESS_TOKEN
        )
        features.append(
            PlatformFeatureFlag(
                key="integrations",
                name="Integraciones externas",
                enabled=integrations_enabled,
                status="ok" if integrations_enabled else "partial",
                reason=None if integrations_enabled else "Sin integraciones externas configuradas",
            )
        )

        # Static features
        features.append(PlatformFeatureFlag(key="low_latency_api", name="API de baja latencia", enabled=True, status="ok"))
        features.append(PlatformFeatureFlag(key="encryption", name="Cifrado y seguridad", enabled=True, status="ok"))

        return PlatformFeaturesResponse(features=features)
