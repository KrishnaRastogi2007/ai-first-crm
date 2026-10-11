from fastapi import FastAPI
from app.api.middleware.request_id import RequestIDMiddleware
from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.health.router import router as health_router

setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
)

app.add_middleware(RequestIDMiddleware)
register_exception_handlers(app)

app.include_router(api_router, prefix="/api/v1")
app.include_router(health_router)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }
