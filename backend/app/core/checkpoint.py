import os
from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from dotenv import load_dotenv
import asyncio

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

@asynccontextmanager
async def get_postgres_checkpointer():
    """
    Context manager loop-safe para obtener el checkpointer.
    Cada test o request obtiene un pool en su propio loop.
    """
    # Crear pool fresco por loop
    pool = AsyncConnectionPool(conninfo=DATABASE_URL, max_size=20, open=False)
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
