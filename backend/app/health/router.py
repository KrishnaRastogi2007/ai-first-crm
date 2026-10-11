"""Application liveness and readiness endpoints."""

import asyncio

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import engine

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Check whether the application is responding."""
    return {
        "status": "healthy",
    }


@router.get("/ready")
async def readiness_check() -> dict[str, str]:
    """Check whether the database is available."""
    try:
        async with asyncio.timeout(2):
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))

    except (TimeoutError, SQLAlchemyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not ready",
        ) from exc

    return {
        "status": "ready",
        "database": "available",
    }