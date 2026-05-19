from typing import List, Dict
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models import User, IAMPolicy, AuditLog, Role
from app.infrastructure.security import get_password_hash
from app.domain.schemas.iam import IAMUserCreate, IAMPolicyAssignRequest
from app.domain.ports.repositories import IAuthRepository

# Mapeo base de políticas conocidas a permisos efectivos
DEFAULT_POLICY_PERMISSIONS: Dict[str, List[str]] = {
    "inventory:read": ["inventory:read"],
    "inventory:write": ["inventory:write"],
    "knowledge:ingest": ["knowledge:ingest"],
    "billing:view": ["billing:view"],
    "chat:use": ["chat:use"],
}

class IAMUseCases:
    def __init__(self, auth_repo: IAuthRepository):
        self.auth_repo = auth_repo

    def ensure_vendor(self, user: User):
        if user.parent_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Solo el vendor principal puede gestionar usuarios limitados"
            )

    async def create_iam_user(
        self, 
        session: AsyncSession, 
        current_user: User, 
        payload: IAMUserCreate,
        invalidate_cache_callback=None
    ) -> User:
        self.ensure_vendor(current_user)

        existing = await self.auth_repo.get_user_by_email(session, payload.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="El correo ya está registrado"
            )

        # Rol mínimo por defecto para usuarios limitados
        role = await self.auth_repo.get_role_by_name(session, "iam_user")
        if not role:
            role = Role(name="iam_user", description="Usuario limitado (IAM)", permissions=[])
            role = await self.auth_repo.create_role(session, role)

        new_user = User(
            email=payload.email,
            password_hash=get_password_hash(payload.password),
            name=payload.name,
            role_id=role.id,
            is_active=True,
            parent_id=current_user.id
        )
        created = await self.auth_repo.create_user(session, new_user)
        
        if invalidate_cache_callback:
            invalidate_cache_callback(created.id)
            
        log = AuditLog(
            user_id=current_user.id, 
            agent_name="iam", 
            action="create_iam_user", 
            details=f"{created.id}"
        )
        session.add(log)
        await session.commit()
        return created

    async def list_iam_users(self, session: AsyncSession, current_user: User) -> List[User]:
        self.ensure_vendor(current_user)
        return await self.auth_repo.get_users_by_parent(session, current_user.id)

    async def get_user_policies(self, session: AsyncSession, current_user: User, user_id: int) -> List[str]:
        self.ensure_vendor(current_user)
        user = await self.auth_repo.get_child_user_by_id(session, current_user.id, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        await session.refresh(user, attribute_names=["policies"])
        return [p.name for p in (user.policies or [])]

    async def set_user_policies(
        self, 
        session: AsyncSession, 
        current_user: User, 
        user_id: int, 
        payload: IAMPolicyAssignRequest,
        invalidate_cache_callback=None
    ) -> User:
        self.ensure_vendor(current_user)
        user = await self.auth_repo.get_child_user_by_id(session, current_user.id, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

        # Resolver políticas por nombre (crearlas si no existen en operación add/set)
        existing_policies = await self.auth_repo.get_policies_by_names(session, payload.policies)
        existing_names = set(p.name for p in existing_policies)
        to_create = [name for name in payload.policies if name not in existing_names]
        created_policies: List[IAMPolicy] = []
        
        if payload.operation in ("set", "add") and to_create:
            for name in to_create:
                perms = DEFAULT_POLICY_PERMISSIONS.get(name, [])
                pol = IAMPolicy(name=name, description=None, permissions=perms)
                created = await self.auth_repo.create_policy(session, pol)
                created_policies.append(created)

        policies = existing_policies + created_policies

        # Cargar colección actual
        await session.refresh(user, attribute_names=["policies"])
        
        if payload.operation == "set":
            user.policies = policies
        elif payload.operation == "add":
            current_set = {p.name: p for p in (user.policies or [])}
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
        
        if invalidate_cache_callback:
            invalidate_cache_callback(user.id)
            
        log = AuditLog(
            user_id=current_user.id, 
            agent_name="iam", 
            action="set_user_policies", 
            details=f"{user.id}:{payload.operation}:{','.join(payload.policies)}"
        )
        session.add(log)
        await session.commit()
        return user

    async def revoke_all_sessions(self, session: AsyncSession, current_user: User, user_id: int):
        self.ensure_vendor(current_user)
        user = await self.auth_repo.get_child_user_by_id(session, current_user.id, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        await self.auth_repo.revoke_all_user_tokens(session, user.id)
        log = AuditLog(
            user_id=current_user.id, 
            agent_name="iam", 
            action="revoke_all_sessions", 
            details=f"{user.id}"
        )
        session.add(log)
        await session.commit()
        return {"ok": True}
