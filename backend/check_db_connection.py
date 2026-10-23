import asyncio
from sqlalchemy import text
from app.db.database import engine

async def main():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT current_user, current_database()")
            )
            print("Database connection successful:", result.fetchone())
    finally:
        await engine.dispose()

asyncio.run(main())
