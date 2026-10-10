from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"app": settings.APP_NAME, "environment": settings.APP_ENV}
