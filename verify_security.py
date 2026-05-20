import os
from dotenv import load_dotenv
from sqlmodel import Session, select
from app.infrastructure.database.session import engine
from app.domain.models import VendorTelegramIntegration
from app.infrastructure.security import decrypt_secret_with_key, encrypt_secret_with_key


def verify_config() -> None:
    load_dotenv()
    secret_key = os.getenv("SECRET_KEY") or ""
    if not secret_key or len(secret_key) < 32:
        print("SECRET_KEY débil o no configurada (se recomienda longitud >= 32 caracteres).")
    else:
        print("SECRET_KEY configurada con longitud adecuada.")


def rotate_telegram_secrets() -> None:
    load_dotenv()
    old_key = os.getenv("OLD_SECRET_KEY")
    new_key = os.getenv("NEW_SECRET_KEY")
    if not old_key or not new_key:
        print("Debes definir OLD_SECRET_KEY y NEW_SECRET_KEY en el entorno para rotar secretos.")
        return
    if old_key == new_key:
        print("OLD_SECRET_KEY y NEW_SECRET_KEY no pueden ser iguales.")
        return
    count = 0
    failed = 0
    with Session(engine) as session:
        integrations = session.exec(select(VendorTelegramIntegration)).all()
        for integration in integrations:
            try:
                plain = decrypt_secret_with_key(integration.bot_token_encrypted, old_key)
                integration.bot_token_encrypted = encrypt_secret_with_key(plain, new_key)
                session.add(integration)
                count += 1
            except Exception:
                failed += 1
        session.commit()
    print(f"Rotación de secretos completada. Actualizados: {count}, fallidos: {failed}.")


if __name__ == "__main__":
    print("Verificando configuración de seguridad...")
    verify_config()
    print("Ejecutando rotación de secretos de Telegram (si se configuraron claves)...")
    rotate_telegram_secrets()
