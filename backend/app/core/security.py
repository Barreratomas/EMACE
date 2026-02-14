from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union
from jose import jwt
from passlib.context import CryptContext
import re
import bleach
import uuid
from app.core.config import settings

# Hashing robusto con bcrypt (salt rounds >= 12 configurado por defecto en passlib para bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def sanitize_html(text: str) -> str:
    """Elimina etiquetas HTML peligrosas para prevenir XSS"""
    if not text:
        return text
    return bleach.clean(text, tags=[], attributes={}, strip=True)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera un hash bcrypt de la contraseña"""
    return pwd_context.hash(password)

def validate_password_policy(password: str) -> tuple[bool, str]:
    """
    Valida la política de contraseñas:
    - Mínimo 12 caracteres (Enterprise Standard)
    - Al menos una mayúscula
    - Al menos una minúscula
    - Al menos un número
    - Al menos un carácter especial
    """
    if len(password) < 12:
        return False, "La contraseña debe tener al menos 12 caracteres."
    if not re.search(r"[A-Z]", password):
        return False, "La contraseña debe tener al menos una letra mayúscula."
    if not re.search(r"[a-z]", password):
        return False, "La contraseña debe tener al menos una letra minúscula."
    if not re.search(r"\d", password):
        return False, "La contraseña debe tener al menos un número."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "La contraseña debe tener al menos un carácter especial."
    
    return True, "Contraseña válida."

def create_password_reset_token(email: str) -> str:
    """Crea un token de un solo uso para recuperación de contraseña"""
    expires_delta = timedelta(hours=1)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": email, "type": "password_reset"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_password_reset_token(token: str) -> Optional[str]:
    """Verifica un token de recuperación y devuelve el email si es válido"""
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if decoded_token.get("type") != "password_reset":
            return None
        return decoded_token.get("sub")
    except jwt.JWTError:
        return None

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None, claims: Optional[dict] = None) -> str:
    """Crea un JWT Access Token de corta duración"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire, 
        "sub": str(subject), 
        "type": "access",
        "jti": str(uuid.uuid4()) # Identificador único para evitar colisiones
    }
    if claims:
        to_encode.update(claims)
        
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Crea un JWT Refresh Token de larga duración"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "exp": expire, 
        "sub": str(subject), 
        "type": "refresh",
        "jti": str(uuid.uuid4()) # Identificador único para evitar colisiones
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """Decodifica un token JWT y devuelve su contenido"""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.JWTError:
        return {}
