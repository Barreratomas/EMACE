from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)


def telegram_webhook_key(request: Request) -> str:
    params = request.path_params or {}
    vendor_public_id = params.get("vendor_public_id", "anon")
    webhook_secret = params.get("webhook_secret", "anon")
    client = get_remote_address(request)
    return f"telegram:{vendor_public_id}:{webhook_secret}:{client}"
