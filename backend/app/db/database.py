"""
Database connection/session.(done)

FastAPI
   ↓
database.py
   ↓
PostgreSQL

Memory:
database.py = DB connection
"""
from sqlalchemy.ext.asyncio import create_async_engine , AsyncSession , async_sessionmaker
from app.core.config import settings
engine = create_async_engine(
    settings.DATABASE_URL,
    echo = False,
    pool_size = 20, # How Many Connections Can Become Opeaned At An Time.
    max_overflow = 30, # How Many Connections Can Be Allowed After Complete Filling Of Pool Connections.
    pool_timeout = 40  # If Connection Not Found Then How Much Time It Hace To Wait.
)
# Session Maker Setup ---->
# SessionLocal Is An Class Or Tempelate Its Work Is To Create Session
SessionLocal = async_sessionmaker(
    bind = engine,
    class_ = AsyncSession, # Tells SQLAlchemy That We Need asynchronous sessions not the synchronous sessions.
    expire_on_commit = False

)

async def get_db():
    async with SessionLocal() as session:
     try:
        yield session
     finally:
        await session.close()