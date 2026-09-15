"""
FastAPI dependencies.

Example:

get_current_user()
get_db()

Memory:

dependencies = cheezein jo endpoint ko chahiye
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.modules.hcp.repository import HCPRepository
from app.modules.hcp.service import HCPService
from app.modules.interaction.repository import InteractionRepository
from app.modules.interaction.service import InteractionService
from app.modules.auth.repository import UserRepository
from app.modules.auth.service import UserService
from app.modules.followup.repository import FollowUpRepository
from app.modules.followup.service import FollowUpService


def get_hcp_service(db:AsyncSession = Depends(get_db)):
    repository = HCPRepository(db)
    return HCPService(repository)

def get_interaction_service(db: AsyncSession = Depends(get_db)):
    repository = InteractionRepository(db)

    return InteractionService(repository)

def get_user_service(
    db: AsyncSession = Depends(get_db)):
    repository = UserRepository(db)

    return UserService(repository)


def get_followup_service(
    db: AsyncSession = Depends(get_db)):
    repository = FollowUpRepository(db)
    return FollowUpService(repository)