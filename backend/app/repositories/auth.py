from typing import List, Optional
from datetime import datetime, timezone
from sqlmodel import Session, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.database.models import User, Role, RefreshToken, IAMPolicy
from sqlmodel import select as sql_select

class AuthRepository:
    # --- User Methods ---
    async def get_user_by_email(self, session: AsyncSession, email: str) -> Optional[User]:
        query = select(User).where(User.email == email).options(selectinload(User.role))
        result = await session.execute(query)
        return result.scalars().first()

    async def get_user_by_id(self, session: AsyncSession, user_id: int) -> Optional[User]:
        query = select(User).where(User.id == user_id).options(selectinload(User.role))
        result = await session.execute(query)
        return result.scalars().first()

    async def create_user(self, session: AsyncSession, user: User) -> User:
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def update_user(self, session: AsyncSession, db_user: User, user_data: dict) -> User:
        for key, value in user_data.items():
            setattr(db_user, key, value)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        return db_user

    # --- Role Methods ---
    async def get_role_by_id(self, session: AsyncSession, role_id: int) -> Optional[Role]:
        query = select(Role).where(Role.id == role_id)
        result = await session.execute(query)
        return result.scalars().first()

    async def get_role_by_name(self, session: AsyncSession, name: str) -> Optional[Role]:
        query = select(Role).where(Role.name == name)
        result = await session.execute(query)
        return result.scalars().first()

    async def create_role(self, session: AsyncSession, role: Role) -> Role:
        session.add(role)
        await session.commit()
        await session.refresh(role)
        return role

    async def get_all_roles(self, session: AsyncSession) -> List[Role]:
        query = select(Role)
        result = await session.execute(query)
        return result.scalars().all()

    # --- IAM Users & Policies ---
    async def get_users_by_parent(self, session: AsyncSession, parent_id: int) -> List[User]:
        query = select(User).where(User.parent_id == parent_id)
        result = await session.execute(query)
        return result.scalars().all()

    async def get_child_user_by_id(self, session: AsyncSession, parent_id: int, child_id: int) -> Optional[User]:
        query = select(User).where(User.id == child_id, User.parent_id == parent_id)
        result = await session.execute(query)
        return result.scalars().first()

    async def get_policy_by_name(self, session: AsyncSession, name: str) -> Optional[IAMPolicy]:
        query = sql_select(IAMPolicy).where(IAMPolicy.name == name)
        result = await session.execute(query)
        return result.scalars().first()

    async def create_policy(self, session: AsyncSession, policy: IAMPolicy) -> IAMPolicy:
        session.add(policy)
        await session.commit()
        await session.refresh(policy)
        return policy

    async def get_policies_by_names(self, session: AsyncSession, names: List[str]) -> List[IAMPolicy]:
        if not names:
            return []
        query = sql_select(IAMPolicy).where(IAMPolicy.name.in_(names))
        result = await session.execute(query)
        return result.scalars().all()

    # --- Refresh Token Methods ---
    async def create_refresh_token(self, session: AsyncSession, token_data: RefreshToken) -> RefreshToken:
        session.add(token_data)
        await session.commit()
        await session.refresh(token_data)
        return token_data

    async def get_refresh_token(self, session: AsyncSession, token: str) -> Optional[RefreshToken]:
        query = select(RefreshToken).where(RefreshToken.token == token, RefreshToken.is_revoked == False)
        result = await session.execute(query)
        return result.scalars().first()

    async def revoke_refresh_token(self, session: AsyncSession, token_id: int) -> None:
        query = select(RefreshToken).where(RefreshToken.id == token_id)
        result = await session.execute(query)
        db_token = result.scalars().first()
        if db_token:
            db_token.is_revoked = True
            session.add(db_token)
            await session.commit()

    async def revoke_all_user_tokens(self, session: AsyncSession, user_id: int) -> None:
        query = select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
        result = await session.execute(query)
        tokens = result.scalars().all()
        for token in tokens:
            token.is_revoked = True
            session.add(token)
        await session.commit()

    async def rotate_refresh_token(self, session: AsyncSession, old_token_id: int, new_token_data: RefreshToken) -> RefreshToken:
        """Revoca un token antiguo y crea uno nuevo en una transacción atómica"""
        # Revocar antiguo
        query = select(RefreshToken).where(RefreshToken.id == old_token_id)
        result = await session.execute(query)
        db_token = result.scalars().first()
        if db_token:
            db_token.is_revoked = True
            session.add(db_token)
        
        # Crear nuevo
        session.add(new_token_data)
        
        await session.commit()
        await session.refresh(new_token_data)
        return new_token_data
