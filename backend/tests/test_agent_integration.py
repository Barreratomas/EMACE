import pytest
import pytest_asyncio
from app.core.config import settings
from app.core.database.models import User, Role, Product, ChatHistory
from sqlmodel import select, text
from app.core.security import get_password_hash, create_access_token
from datetime import datetime

@pytest_asyncio.fixture(scope="function")
async def test_data(db_session):
    """Crea datos de prueba básicos usando la sesión del test."""
    
    # 1. Crear Roles
    result = await db_session.execute(select(Role).where(Role.name == "admin"))
    admin_role = result.scalars().first()
    if not admin_role:
        admin_role = Role(name="admin", permissions=["billing:access", "tech:access", "sales:access", "inventory:access"])
        db_session.add(admin_role)
    
    result = await db_session.execute(select(Role).where(Role.name == "limited_user"))
    limited_role = result.scalars().first()
    if not limited_role:
        limited_role = Role(name="limited_user", permissions=["tech:access"])
        db_session.add(limited_role)
    
    await db_session.flush()

    # 2. Crear Usuarios
    result = await db_session.execute(select(User).where(User.email == "user1@example.com"))
    user1 = result.scalars().first()
    if not user1:
        user1 = User(
            name="User One (Admin)",
            email="user1@example.com",
            password_hash=get_password_hash("Password123!"),
            role_id=admin_role.id,
            is_active=True
        )
        db_session.add(user1)

    result = await db_session.execute(select(User).where(User.email == "user2@example.com"))
    user2 = result.scalars().first()
    if not user2:
        user2 = User(
            name="User Two (Limited)",
            email="user2@example.com",
            password_hash=get_password_hash("Password123!"),
            role_id=limited_role.id,
            is_active=True
        )
        db_session.add(user2)

    await db_session.flush()

    # 3. Crear Productos
    p1_name = "Laptop HP Pro x360"
    p2_name = "Servidor Dell PowerEdge"
    
    p1 = Product(name=p1_name, category="Hardware", price=1200.0, description="Laptop corporativa", user_id=user1.id, stock=10, type="physical")
    db_session.add(p1)

    p2 = Product(name=p2_name, category="Hardware", price=5500.0, description="Servidor datacenter", user_id=user2.id, stock=5, type="physical")
    db_session.add(p2)

    await db_session.commit()
    
    return {
        "user1_token": create_access_token(user1.id),
        "user2_token": create_access_token(user2.id),
        "user1_id": user1.id,
        "user2_id": user2.id,
        "p1_name": p1_name,
        "p2_name": p2_name
    }

@pytest.mark.asyncio
async def test_rbac_supervisor_restriction(client, test_data):
    """Verifica que el Supervisor restringe el acceso basado en permisos del rol."""
    headers = {"Authorization": f"Bearer {test_data['user2_token']}"}
    response = await client.post(
        f"{settings.API_V1_STR}/chat",
        json={"message": "Quiero ver las ventas de hoy", "thread_id": "test_rbac_1"},
        headers=headers
    )
    assert response.status_code == 200
    response_text = response.json()["response"].lower()
    print(f"DEBUG RBAC Response: {response_text}")
    
    # El supervisor debe denegar si no tiene sales:access
    assert any(x in response_text for x in ["no puedo", "no tengo", "no está permitido", "acceso denegado", "permisos", "lo siento"])

@pytest.mark.asyncio
async def test_multi_tenant_isolation_sql(client, test_data, db_session):
    """Verifica que un usuario no puede ver productos de otro usuario."""
    # User 1 pregunta por sus productos
    headers1 = {"Authorization": f"Bearer {test_data['user1_token']}"}
    response1 = await client.post(
        f"{settings.API_V1_STR}/chat",
        json={"message": f"Lista mis productos que contengan '{test_data['p1_name']}'", "thread_id": "test_isolation_1"},
        headers=headers1
    )
    assert response1.status_code == 200
    resp1_text = response1.json()["response"]
    print(f"DEBUG Isolation 1 Response: {resp1_text}")
    assert test_data["p1_name"] in resp1_text
    assert test_data["p2_name"] not in resp1_text

    # User 2 pregunta por sus productos (dándole permiso de ventas primero)
    # Cargar el rol explícitamente y actualizarlo
    from sqlalchemy.orm import selectinload
    result = await db_session.execute(
        select(User).where(User.id == test_data["user2_id"]).options(selectinload(User.role))
    )
    u2 = result.scalars().first()
    
    role = u2.role
    # Asegurarnos de que tenga los permisos necesarios
    new_perms = list(set(role.permissions + ["sales:access", "inventory:access"]))
    role.permissions = new_perms
    db_session.add(role)
    await db_session.commit()
    
    # IMPORTANTE: Expire para que la próxima vez que se cargue (en el endpoint) sea de la DB
    db_session.expire_all()

    headers2 = {"Authorization": f"Bearer {test_data['user2_token']}"}
    # Usar un thread_id único para evitar interferencias de memoria de LangGraph
    response2 = await client.post(
        f"{settings.API_V1_STR}/chat",
        json={"message": f"Lista mis productos que contengan '{test_data['p2_name']}'", "thread_id": "test_isolation_u2_new"},
        headers=headers2
    )
    assert response2.status_code == 200
    resp2_text = response2.json()["response"]
    print(f"DEBUG Isolation 2 Response: {resp2_text}")
    assert test_data["p2_name"] in resp2_text
    assert test_data["p1_name"] not in resp2_text

@pytest.mark.asyncio
async def test_audit_logs_contain_user_id(client, test_data, db_session):
    """Verifica que los logs de auditoría (ChatHistory) guardan el user_id."""
    headers = {"Authorization": f"Bearer {test_data['user1_token']}"}
    unique_id = f"{datetime.now().timestamp()}_{test_data['user1_id']}"
    msg = f"Audit test message {unique_id}"
    
    await client.post(
        f"{settings.API_V1_STR}/chat",
        json={"message": msg, "thread_id": f"test_audit_{unique_id}"},
        headers=headers
    )
    
    # Verificar en la base de datos buscando el mensaje exacto
    db_session.expire_all()
    result = await db_session.execute(
        select(ChatHistory).where(
            ChatHistory.user_id == test_data["user1_id"],
            ChatHistory.user_message == msg
        )
    )
    history = result.scalars().first()
    assert history is not None
    assert history.user_id == test_data["user1_id"]
    assert history.user_message == msg
