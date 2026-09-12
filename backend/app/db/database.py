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
from sqlalchemy.ext.asyncio import create_async_engine
"""
from sqlalchemy.ext.asyncio import create_async_engine --->
"""
from app.core.config import settings
engine = create_async_engine(settings.DATABASE_URL,echo = True)