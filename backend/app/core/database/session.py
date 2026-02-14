from sqlmodel import create_engine, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
import os

settings = get_settings()

# Motor Síncrono (Legacy/Audit/Tools)
engine = create_engine(settings.DATABASE_URL, echo=False)

# Motor Asíncrono (Principal)
ASYNC_DATABASE_URL = settings.DATABASE_URL.replace(
    "postgresql://", "postgresql+psycopg://"
)

_async_engine = None
_async_sessionmaker = None

def get_async_engine():
    global _async_engine
    if _async_engine is None:
        _async_engine = create_async_engine(
            ASYNC_DATABASE_URL,
            echo=False,
            future=True,
            pool_pre_ping=True,
        )
    return _async_engine

def get_async_sessionmaker():
    global _async_sessionmaker
    if _async_sessionmaker is None:
        _async_sessionmaker = sessionmaker(
            get_async_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_sessionmaker

def get_session():
    """Sesión síncrona para tools / scripts / legacy"""
    with Session(engine) as session:
        yield session

async def get_async_session():
    """Dependencia principal para sesiones asíncronas"""
    async_session = get_async_sessionmaker()
    async with async_session() as session:
        yield session
