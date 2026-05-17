import asyncio
import sys
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.api.main import app
from app.core.database.session import ASYNC_DATABASE_URL, get_async_session
from app.core.config import settings

# FIX CRÍTICO PARA WINDOWS
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@pytest_asyncio.fixture(scope="session")
async def engine():
    """Motor de base de datos para toda la sesión de tests."""
    # Usar psycopg (v3) que es más estable con el ciclo de vida del loop
    engine = create_async_engine(
        ASYNC_DATABASE_URL,
        echo=False,
        future=True,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def db_session(engine):
    """
    Sesión de base de datos por test.
    Usa transacciones para limpiar datos automáticamente.
    """
    connection = await engine.connect()
    trans = await connection.begin()
    
    # Sessionmaker ligado a esta conexión específica
    async_session = AsyncSession(
        bind=connection, 
        expire_on_commit=False,
        join_transaction_mode="rollback_only" # Importante para tests
    )

    yield async_session

    await async_session.close()
    await trans.rollback()
    await connection.close()

@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """
    Cliente HTTP que inyecta la db_session del test en la app.
    """
    from httpx import AsyncClient, ASGITransport

    async def override_get_async_session():
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_async_session
    
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test",
        timeout=30.0
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()
