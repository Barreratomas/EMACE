from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database.session import get_async_session
from app.core.database.models import User, RefreshToken, Role
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    validate_password_policy
)
from app.core.config import settings
from app.schemas.auth import Token, UserLogin, UserRegister, UserResponse, PasswordChange, UserUpdate
from app.repositories.auth import AuthRepository
from app.api.deps import get_current_user
from app.core.rate_limit import limiter

router = APIRouter()
auth_repo = AuthRepository()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_in: UserRegister,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Registrar un nuevo usuario (Vendor).
    """
    # Validar política de contraseñas
    is_valid, message = validate_password_policy(user_in.password)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    # Verificar si el email ya existe
    existing_user = await auth_repo.get_user_by_email(session, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado"
        )

    # Obtener o crear rol por defecto (vendor)
    role = await auth_repo.get_role_by_name(session, "vendor")
    if not role:
        role = Role(name="vendor", description="Vendedor / Dueño de tienda")
        role = await auth_repo.create_role(session, role)

    # Crear usuario
    new_user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        name=user_in.name,
        role_id=role.id,
        is_active=True
    )
    return await auth_repo.create_user(session, new_user)

@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session)
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = await auth_repo.get_user_by_email(session, form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo")

    # Generar tokens
    access_token = create_access_token(
        subject=user.id,
        claims={"role": user.role.name if user.role else None}
    )
    refresh_token_str = create_refresh_token(subject=user.id)

    # Guardar refresh token en BD
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db_refresh_token = RefreshToken(
        token=refresh_token_str,
        user_id=user.id,
        expires_at=expires_at
    )
    await auth_repo.create_refresh_token(session, db_refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
    }

@router.post("/refresh", response_model=Token)
async def refresh_token_endpoint(
    token_str: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Rotar refresh token y obtener nuevo access token.
    """
    db_token = await auth_repo.get_refresh_token(session, token_str)
    if not db_token or db_token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado"
        )

    user = await auth_repo.get_user_by_id(session, db_token.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado o inactivo")

    # Generar nuevos tokens
    new_access_token = create_access_token(
        subject=user.id,
        claims={"role": user.role.name if user.role else None}
    )
    new_refresh_token_str = create_refresh_token(subject=user.id)

    # Rotar en BD
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_db_refresh_token = RefreshToken(
        token=new_refresh_token_str,
        user_id=user.id,
        expires_at=expires_at
    )
    await auth_repo.rotate_refresh_token(session, db_token.id, new_db_refresh_token)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token_str,
        "token_type": "bearer",
    }

@router.post("/logout")
async def logout(
    token_str: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Revocar un refresh token específico.
    """
    db_token = await auth_repo.get_refresh_token(session, token_str)
    if db_token and db_token.user_id == current_user.id:
        await auth_repo.revoke_refresh_token(session, db_token.id)
    return {"detail": "Sesión cerrada exitosamente"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Obtener información del usuario actual.
    """
    return current_user

@router.patch("/me", response_model=UserResponse)
async def update_me(
    user_update: UserUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Actualizar perfil del usuario actual.
    """
    update_data = user_update.model_dump(exclude_unset=True)
    
    if "email" in update_data and update_data["email"] != current_user.email:
        existing_user = await auth_repo.get_user_by_email(session, update_data["email"])
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email ya registrado")
            
    return await auth_repo.update_user(session, current_user, update_data)

@router.post("/me/change-password")
async def change_password(
    pwd_in: PasswordChange,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Cambiar contraseña del usuario actual.
    """
    if not verify_password(pwd_in.old_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contraseña actual incorrecta")
        
    is_valid, message = validate_password_policy(pwd_in.new_password)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
        
    await auth_repo.update_user(
        session, 
        current_user, 
        {"password_hash": get_password_hash(pwd_in.new_password)}
    )
    return {"detail": "Contraseña actualizada exitosamente"}
