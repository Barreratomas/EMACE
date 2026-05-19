from typing import AsyncGenerator, Optional, List, Set
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from cachetools import TTLCache

from app.infrastructure.config import settings
from app.infrastructure.database.session import get_async_session
from app.domain.models import User, VendorAccessState
from app.infrastructure.repositories.auth import AuthRepository
from app.infrastructure.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

auth_repo = AuthRepository()

async def get_current_user(
    session: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme)
) -> User:
    """Dependencia para obtener el usuario actual validando el JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if not payload:
        raise credentials_exception
        
    user_id: str = payload.get("sub")
    token_type: str = payload.get("type")
    
    if user_id is None or token_type != "access":
        raise credentials_exception
        
    # Cargar usuario con su rol y políticas IAM
    query = select(User).where(User.id == int(user_id)).options(
        selectinload(User.role),
        selectinload(User.policies)
    )
    result = await session.execute(query)
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Usuario inactivo"
        )
        
    return user

# --- Permisos efectivos con caché (TTL) ---
_PERMISSIONS_CACHE: TTLCache[int, Set[str]] = TTLCache(maxsize=10000, ttl=60)

def get_effective_permissions(user: User) -> Set[str]:
    cached = _PERMISSIONS_CACHE.get(user.id)
    if cached is not None:
        return cached
    effective: Set[str] = set()
    if user.role and user.role.permissions:
        effective.update(user.role.permissions)
    if getattr(user, "policies", None):
        for pol in user.policies:
            if pol.permissions:
                effective.update(pol.permissions)
    _PERMISSIONS_CACHE[user.id] = effective
    return effective

def invalidate_permissions_cache_for_user(user_id: int) -> None:
    try:
        del _PERMISSIONS_CACHE[user_id]
    except KeyError:
        pass

class RoleChecker:
    """Verificador de roles para RBAC + IAM Policies."""
    def __init__(self, allowed_roles: List[str], required_permissions: Optional[List[str]] = None):
        self.allowed_roles = allowed_roles
        self.required_permissions = required_permissions or []

    def __call__(self, user: User = Depends(get_current_user)):
        # Verificar rol
        role_ok = user.role and user.role.name in self.allowed_roles if self.allowed_roles else True
        # Permisos efectivos con caché (rol.permissions ∪ policies[].permissions)
        effective_permissions = get_effective_permissions(user)
        perms_ok = all(p in effective_permissions for p in self.required_permissions) if self.required_permissions else True
        if not (role_ok and perms_ok):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos suficientes para realizar esta acción")
        return user

def get_current_active_admin(user: User = Depends(get_current_user)) -> User:
    """Dependencia rápida para requerir rol admin"""
    if not user.role or user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren privilegios de administrador"
        )
    return user
    return user

def get_tenant_owner_id(user: User) -> int:
    return user.parent_id if user.parent_id is not None else user.id


async def require_access(
    request: Request,
    premium: bool = False,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_user),
):
    """
    Enforcement de acceso:
    - lifetime: acceso total.
    - subscription: acceso si valid_until futuro.
    - trial: acceso total salvo premium si expirado.
    """
    # Intentar leer del middleware (si existe)
    access = getattr(request.state, "vendor_access", None)
    now_valid = None
    mode = None
    source = None
    if access:
        mode = access.get("access_mode")
        source = access.get("source")
        now_valid = access.get("valid")  # bool
    else:
        # Fallback a DB
        result = await session.execute(
            select(VendorAccessState).where(VendorAccessState.vendor_id == (user.parent_id or user.id))
        )
        state = result.scalars().first()
        if state:
            mode = state.access_mode
            source = state.source
            if mode == "lifetime":
                now_valid = True
            elif state.valid_until:
                from datetime import datetime, timezone
                now_valid = state.valid_until > datetime.now(timezone.utc)
            else:
                now_valid = False
        else:
            # Si no hay estado, permitir (por backward-compat) excepto premium estricto
            if premium:
                raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Funcionalidad premium requiere plan activo")
            return

    # Reglas
    if mode == "lifetime":
        return
    if source == "paid_subscription":
        if now_valid:
            return
        # Suscripción expirada → tratar como degradado
        if premium:
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Suscripción expirada. Renueva para acceder a esta funcionalidad premium.")
        return
    if source == "trial":
        if now_valid:
            return
        if premium:
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="El trial expiró. Suscríbete para continuar con funcionalidades premium.")
        return
