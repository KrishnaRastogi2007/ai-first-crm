from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.followups import router as followup_router
from app.api.v1.hcps import router as hcp_router
from app.api.v1.interactions import router as interaction_router
from app.api.v1.users import router as users_router
from app.api.v1.chat import router as chat_router

api_router = APIRouter()


api_router.include_router(auth_router)
api_router.include_router(hcp_router)
api_router.include_router(interaction_router)
api_router.include_router(followup_router)
api_router.include_router(users_router)
api_router.include_router(chat_router)