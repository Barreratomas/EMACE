from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models import User, Role, VendorAccessState, RefreshToken
from app.domain.schemas.auth import UserRegister, IAMLogin
from app.domain.schemas.user import UserUpdate, PasswordChange
from app.domain.ports.repositories import IAuthRepository
from app.infrastructure.security import (
    get_password_hash, 
    verify_password, 
    validate_password_policy,
    create_access_token,
    create_refresh_token as create_jwt_refresh_token
)
from app.infrastructure.config import settings

class AuthUseCases:
    def __init__(self, auth_repo: IAuthRepository):
        self.auth_repo = auth_repo

    async def register_vendor(self, session: AsyncSession, user_in: UserRegister) -> User:
        # Validar política de contraseñas
        is_valid, message = validate_password_policy(user_in.password)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

        # Verificar si el email ya existe
        existing_user = await self.auth_repo.get_user_by_email(session, user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está registrado"
            )

        # Obtener o crear rol por defecto (vendor)
        role = await self.auth_repo.get_role_by_name(session, "vendor")
        if not role:
            role = Role(name="vendor", description="Vendedor / Dueño de Tienda")
            role = await self.auth_repo.create_role(session, role)

        # Crear nuevo usuario
        new_user = User(
            name=user_in.name,
            email=user_in.email,
            password_hash=get_password_hash(user_in.password),
            role_id=role.id,
            is_active=True,
            plan_type="basic"
        )
        
        created_user = await self.auth_repo.create_user(session, new_user)

        # Estado de acceso inicial (Trial 30 días)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        trial_until = now + timedelta(days=30)
        vas = VendorAccessState(
            vendor_id=created_user.id,
            access_mode="subscription",
            source="trial",
            valid_until=trial_until,
            subscription_id_mp=None,
            created_at=now
        )
        session.add(vas)
        await session.commit()

        return created_user

    async def login(self, session: AsyncSession, username: str, password: str) -> Dict[str, Any]:
        user = await self.auth_repo.get_user_by_email(session, username)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo")
        
        if user.parent_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario limitado detectado. Debes iniciar sesión en la sección de Usuarios Limitados."
            )

        return await self._generate_tokens_and_save(session, user)

    async def login_iam(self, session: AsyncSession, body: IAMLogin) -> Dict[str, Any]:
        vendor = await self.auth_repo.get_user_by_email(session, body.vendor_identifier)
        if not vendor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor no encontrado")

        user = await self.auth_repo.get_user_by_email(session, body.email)
        if not user or not verify_password(body.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo")
        if user.parent_id != vendor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El usuario no pertenece al vendor indicado")

        return await self._generate_tokens_and_save(session, user, is_iam=True, vendor_id=vendor.id)

    async def refresh_token(self, session: AsyncSession, token_str: str) -> Dict[str, Any]:
        db_token = await self.auth_repo.get_refresh_token(session, token_str)
        if not db_token or db_token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido o expirado"
            )

        user = await self.auth_repo.get_user_by_id(session, db_token.user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado o inactivo")

        user_type = "iam_user" if user.parent_id is not None else "vendor"
        vendor_parent_id = user.parent_id if user.parent_id is not None else user.id
        
        new_access_token = create_access_token(
            subject=user.id,
            claims={
                "role": user.role.name if user.role else None,
                "user_type": user_type,
                "vendor_parent_id": vendor_parent_id
            }
        )
        new_refresh_token_str = create_jwt_refresh_token(subject=user.id)

        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        new_db_refresh_token = RefreshToken(
            token=new_refresh_token_str,
            user_id=user.id,
            expires_at=expires_at
        )
        await self.auth_repo.rotate_refresh_token(session, db_token.id, new_db_refresh_token)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token_str,
            "token_type": "bearer",
        }

    async def logout(self, session: AsyncSession, user_id: int, token_str: str) -> bool:
        db_token = await self.auth_repo.get_refresh_token(session, token_str)
        if db_token and db_token.user_id == user_id:
            await self.auth_repo.revoke_refresh_token(session, db_token.id)
            return True
        return False

    async def update_user_me(self, session: AsyncSession, current_user: User, user_update: UserUpdate) -> User:
        update_data = user_update.model_dump(exclude_unset=True)
        
        if "email" in update_data and update_data["email"] != current_user.email:
            existing_user = await self.auth_repo.get_user_by_email(session, update_data["email"])
            if existing_user:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email ya registrado")
                
        return await self.auth_repo.update_user(session, current_user, update_data)

    async def change_password(self, session: AsyncSession, current_user: User, pwd_in: PasswordChange) -> None:
        if not verify_password(pwd_in.old_password, current_user.password_hash):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contraseña actual incorrecta")
            
        is_valid, message = validate_password_policy(pwd_in.new_password)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
            
        await self.auth_repo.update_user(
            session, 
            current_user, 
            {"password_hash": get_password_hash(pwd_in.new_password)}
        )

    async def _generate_tokens_and_save(self, session: AsyncSession, user: User, is_iam: bool = False, vendor_id: Optional[int] = None) -> Dict[str, Any]:
        user_type = "iam_user" if is_iam else "vendor"
        vendor_parent_id = vendor_id if is_iam else user.id
        
        access_token = create_access_token(
            subject=user.id,
            claims={
                "role": user.role.name if user.role else None,
                "user_type": user_type,
                "vendor_parent_id": vendor_parent_id
            }
        )
        refresh_token_str = create_jwt_refresh_token(subject=user.id)

        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        db_refresh_token = RefreshToken(
            token=refresh_token_str,
            user_id=user.id,
            expires_at=expires_at
        )
        await self.auth_repo.create_refresh_token(session, db_refresh_token)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token_str,
            "token_type": "bearer",
        }
