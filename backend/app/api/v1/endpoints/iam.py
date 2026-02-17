from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.core.database.session import get_async_session
from app.core.database.models import User, IAMPolicy, AuditLog
from app.api.deps import get_current_user, invalidate_permissions_cache_for_user
from app.core.security import get_password_hash
from app.schemas.auth import IAMUserCreate, IAMUserResponse, IAMPolicyAssignRequest, UserResponse
from app.repositories.auth import AuthRepository
from app.core.rate_limit import limiter

router = APIRouter()
auth_repo = AuthRepository()

# Mapeo base de políticas conocidas a permisos efectivos
DEFAULT_POLICY_PERMISSIONS: Dict[str, List[str]] = {
    "inventory:read": ["inventory:read"],
    "inventory:write": ["inventory:write"],
    "knowledge:ingest": ["knowledge:ingest"],
    "billing:view": ["billing:view"],
    "chat:use": ["chat:use"],
}

def ensure_vendor(user: User):
    if user.parent_id is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo el vendor principal puede gestionar usuarios limitados")


@router.post("/users", response_model=IAMUserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_iam_user(
    request: Request,
    payload: IAMUserCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Crear un usuario limitado asociado al vendor actual.
    """
    ensure_vendor(current_user)

    existing = await auth_repo.get_user_by_email(session, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El correo ya está registrado")

    # Rol mínimo por defecto para usuarios limitados
    role = await auth_repo.get_role_by_name(session, "iam_user")
    if not role:
        from app.core.database.models import Role
        role = Role(name="iam_user", description="Usuario limitado (IAM)", permissions=[])
        role = await auth_repo.create_role(session, role)

    new_user = User(
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        name=payload.name,
        role_id=role.id,
        is_active=True,
        parent_id=current_user.id
    )
    created = await auth_repo.create_user(session, new_user)
    invalidate_permissions_cache_for_user(created.id)
    log = AuditLog(user_id=current_user.id, agent_name="iam", action="create_iam_user", details=f"{created.id}")
    session.add(log)
    await session.commit()
    return created


@router.get("/users", response_model=List[UserResponse])
@limiter.limit("10/minute")
async def list_iam_users(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Listar usuarios limitados del vendor actual.
    """
    ensure_vendor(current_user)
    users = await auth_repo.get_users_by_parent(session, current_user.id)
    return users


@router.get("/users/{user_id}/policies", response_model=List[str])
@limiter.limit("10/minute")
async def get_user_policies(
    request: Request,
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener los nombres de las políticas asignadas a un usuario limitado del equipo.
    """
    ensure_vendor(current_user)
    user = await auth_repo.get_child_user_by_id(session, current_user.id, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    await session.refresh(user, attribute_names=["policies"])
    return [p.name for p in (user.policies or [])]


@router.patch("/users/{user_id}/policies", response_model=IAMUserResponse)
@limiter.limit("10/minute")
async def set_user_policies(
    request: Request,
    user_id: int,
    payload: IAMPolicyAssignRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Asignar/remover políticas IAM a un usuario del equipo.
    operation: set | add | remove
    """
    ensure_vendor(current_user)
    user = await auth_repo.get_child_user_by_id(session, current_user.id, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    # Resolver políticas por nombre (crearlas si no existen en operación add/set)
    existing_policies = await auth_repo.get_policies_by_names(session, payload.policies)
    existing_names = set(p.name for p in existing_policies)
    to_create = [name for name in payload.policies if name not in existing_names]
    created_policies: List[IAMPolicy] = []
    if payload.operation in ("set", "add") and to_create:
        for name in to_create:
            perms = DEFAULT_POLICY_PERMISSIONS.get(name, [])
            pol = IAMPolicy(name=name, description=None, permissions=perms)
            created = await auth_repo.create_policy(session, pol)
            created_policies.append(created)

    policies = existing_policies + created_policies

    # Cargar colección actual
    await session.refresh(user)
    await session.refresh(user, attribute_names=["policies"])
    current_set = {p.name: p for p in (user.policies or [])}

    if payload.operation == "set":
        user.policies = policies
    elif payload.operation == "add":
        for pol in policies:
            current_set[pol.name] = pol
        user.policies = list(current_set.values())
    elif payload.operation == "remove":
        to_remove = set(payload.policies)
        user.policies = [p for p in (user.policies or []) if p.name not in to_remove]
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Operación inválida")

    session.add(user)
    await session.commit()
    await session.refresh(user)
    invalidate_permissions_cache_for_user(user.id)
    log = AuditLog(user_id=current_user.id, agent_name="iam", action="set_user_policies", details=f"{user.id}:{payload.operation}:{','.join(payload.policies)}")
    session.add(log)
    await session.commit()
    return user

@router.post("/users/{user_id}/sessions/revoke-all")
@limiter.limit("5/minute")
async def revoke_all_sessions(
    request: Request,
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    ensure_vendor(current_user)
    user = await auth_repo.get_child_user_by_id(session, current_user.id, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    await auth_repo.revoke_all_user_tokens(session, user.id)
    log = AuditLog(user_id=current_user.id, agent_name="iam", action="revoke_all_sessions", details=f"{user.id}")
    session.add(log)
    await session.commit()
    return {"ok": True}
