import asyncio
from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy.engine.url import make_url
from app.infrastructure.config import get_settings

settings = get_settings()

def _build_conninfo() -> str:
  url = make_url(settings.DATABASE_URL)
  userinfo = ""
  if url.username:
    userinfo = url.username
    if url.password:
      userinfo += f":{url.password}"
    userinfo += "@"
  host = url.host or "localhost"
  port = f":{url.port}" if url.port else ""
  database = url.database or ""
  return f"postgresql://{userinfo}{host}{port}/{database}"

@asynccontextmanager
async def get_postgres_checkpointer():
    """
    Context manager loop-safe para obtener el checkpointer.
    Cada test o request obtiene un pool en su propio loop.
    """
    pool = AsyncConnectionPool(conninfo=_build_conninfo(), max_size=20, open=False)
    await pool.open()
    print(f"DEBUG: Pool opened for loop {id(asyncio.get_running_loop())}")

    # Setup checkpointer tables por pool
    async with pool.connection() as conn:
        await conn.set_autocommit(True)
        checkpointer = AsyncPostgresSaver(conn)
        await checkpointer.setup()
        print("DEBUG: Setup finished")

    # Devolver checkpointer ligado al pool
    checkpointer = AsyncPostgresSaver(pool)
    try:
        yield checkpointer
    finally:
        await pool.close()
        print("DEBUG: Pool closed for loop", id(asyncio.get_running_loop()))
