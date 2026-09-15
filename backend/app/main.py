# Starting Point Of Fast API Application

"""
Its Work Is To  --- Create FastAPI app 
--- Including Routs
--- Application Startup Configuration 
----- It Not Contails Working / Business Logic 


Yahin:

FastAPI application create
routers register
middleware
startup/shutdown
global configuration

etc. connect honge.

"""

from fastapi import FastAPI

from app.core.config import settings
from app.api.v1.hcps import router as hcp_router
from app.api.v1.interactions import router as interaction_router
from app.modules.auth.models import Users
from app.api.v1.auth import router as user_router
from app.api.v1.followups import router as followup_router

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0"
)


app.include_router(
    hcp_router,
    prefix="/api/v1"
)

app.include_router(
    interaction_router,
    prefix="/api/v1"
)

app.include_router(
    user_router,
    prefix="/api/v1"
)

app.include_router(
    followup_router,
    prefix="/api/v1"
)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV
    }
# uvicorn --app-dir backend app.main:app --reload