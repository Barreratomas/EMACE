from typing import List
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.session import get_async_session
from app.domain.models import User
from app.interfaces.api.deps import get_current_user, invalidate_permissions_cache_for_user
from app.domain.schemas.iam import IAMUserCreate, IAMUserResponse, IAMPolicyAssignRequest
from app.domain.schemas.user import UserResponse
from app.infrastructure.repositories.auth import AuthRepository
from app.infrastructure.repositories.audit import audit_repo
from app.infrastructure.adapters.rate_limit import limiter
from app.application.use_cases.iam_use_cases import IAMUseCases

router = APIRouter()
auth_repo = AuthRepository()
iam_use_cases = IAMUseCases(auth_repo, audit_repo)

@router.post("/users", response_model=IAMUserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_iam_user(
    request: Request,
    payload: IAMUserCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Crea un usuario limitado (IAM) vinculado a la cuenta del vendor actual"""
    return await iam_use_cases.create_iam_user(
        session, 
        current_user, 
        payload, 
        invalidate_cache_callback=invalidate_permissions_cache_for_user
    )


@router.get("/users", response_model=List[UserResponse])
@limiter.limit("10/minute")
async def list_iam_users(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Lista todos los usuarios IAM creados por el vendor"""
    return await iam_use_cases.list_iam_users(session, current_user)


@router.get("/users/{user_id}/policies", response_model=List[str])
@limiter.limit("10/minute")
async def get_user_policies(
    request: Request,
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Obtiene las políticas de permisos asignadas a un usuario específico"""
    return await iam_use_cases.get_user_policies(session, current_user, user_id)


@router.patch("/users/{user_id}/policies", response_model=IAMUserResponse)
@limiter.limit("10/minute")
async def set_user_policies(
    request: Request,
    user_id: int,
    payload: IAMPolicyAssignRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Modifica (añade, elimina o sobrescribe) las políticas de un usuario IAM"""
    return await iam_use_cases.set_user_policies(
        session, 
        current_user, 
        user_id, 
        payload, 
        invalidate_cache_callback=invalidate_permissions_cache_for_user
    )

@router.post("/users/{user_id}/sessions/revoke-all")
@limiter.limit("5/minute")
async def revoke_all_sessions(
    request: Request,
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Revoca inmediatamente todas las sesiones activas de un usuario IAM"""
    return await iam_use_cases.revoke_all_sessions(session, current_user, user_id)
