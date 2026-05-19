from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.session import get_async_session
from app.domain.models import User
from app.domain.schemas.auth import UserRegister, IAMLogin
from app.domain.schemas.token import Token
from app.domain.schemas.user import UserResponse, PasswordChange, UserUpdate
from app.infrastructure.repositories.auth import AuthRepository
from app.interfaces.api.deps import get_current_user
from app.infrastructure.adapters.rate_limit import limiter
from app.application.use_cases.auth_use_cases import AuthUseCases

router = APIRouter()
auth_repo = AuthRepository()
auth_use_cases = AuthUseCases(auth_repo)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_in: UserRegister,
    session: AsyncSession = Depends(get_async_session)
):
    """Registra un nuevo usuario vendor y crea su periodo de prueba inicial"""
    return await auth_use_cases.register_vendor(session, user_in)

@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session)
):
    """Autenticación estándar para administradores y vendors mediante OAuth2"""
    return await auth_use_cases.login(session, form_data.username, form_data.password)

@router.post("/login-iam", response_model=Token)
@limiter.limit("10/minute")
async def login_iam(
    request: Request,
    body: IAMLogin,
    session: AsyncSession = Depends(get_async_session)
):
    """Login particionado para usuarios limitados (IAM)"""
    return await auth_use_cases.login_iam(session, body)

@router.post("/refresh", response_model=Token)
async def refresh_token_endpoint(
    token_str: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Rotar refresh token y obtener nuevo access token"""
    return await auth_use_cases.refresh_token(session, token_str)

@router.post("/logout")
async def logout(
    token_str: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Revocar un refresh token específico y cerrar la sesión"""
    await auth_use_cases.logout(session, current_user.id, token_str)
    return {"detail": "Sesión cerrada exitosamente"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Obtener información del perfil del usuario autenticado actualmente"""
    return current_user

@router.patch("/me", response_model=UserResponse)
async def update_me(
    user_update: UserUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Actualizar los datos del perfil del usuario actual"""
    return await auth_use_cases.update_user_me(session, current_user, user_update)

@router.post("/me/change-password")
async def change_password(
    pwd_in: PasswordChange,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Cambiar la contraseña de acceso del usuario actual"""
    await auth_use_cases.change_password(session, current_user, pwd_in)
    return {"detail": "Contraseña actualizada correctamente"}
