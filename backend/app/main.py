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


from app.api.router import api_router

app = FastAPI(title=settings.APP_NAME,version="1.0.0")

app.include_router(api_router,prefix="/api/v1")


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV
    }
# uvicorn --app-dir backend app.main:app --reload