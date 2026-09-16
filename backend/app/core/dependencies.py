"""
FastAPI dependencies.

Example:

get_current_user()
get_db()

Memory:

dependencies = cheezein jo endpoint ko chahiye
"""
from fastapi import Depends ,HTTPException , status
from fastapi.security import OAuth2PasswordBearer
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
from app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


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

async def get_current_user(token: str = Depends(oauth2_scheme),db: AsyncSession = Depends(get_db)):
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Or Expired Token"
        )

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token"
        )

    repository = UserRepository(db)

    user = await repository.get_by_id(int(user_id))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User Not Found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive User"
        )

    return user
