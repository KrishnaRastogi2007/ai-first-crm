from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import Permission, has_permission
from app.core.security import decode_access_token
from app.db.database import get_db
from app.modules.auth.repository import UserRepository
from app.modules.auth.service import UserService
from app.modules.followup.repository import FollowUpRepository
from app.modules.followup.service import FollowUpService
from app.modules.hcp.repository import HCPRepository
from app.modules.hcp.service import HCPService
from app.modules.interaction.repository import InteractionRepository
from app.modules.interaction.service import InteractionService

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)


def get_hcp_service(db: AsyncSession = Depends(get_db)):
    hcp_repository = HCPRepository(db)
    user_repository = UserRepository(db)

    return HCPService(
        repository=hcp_repository,
        user_repository=user_repository,
    )


def get_interaction_service(db: AsyncSession = Depends(get_db)):
    repository = InteractionRepository(db)
    return InteractionService(repository)


def get_user_service(db: AsyncSession = Depends(get_db)):
    repository = UserRepository(db)
    return UserService(repository)


def get_followup_service(db: AsyncSession = Depends(get_db)):
    repository = FollowUpRepository(db)
    return FollowUpService(repository)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    # Step 1: Access token validate karo
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Step 2: Token se user ID nikalo
    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Step 3: User ID ka format validate karo
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Step 4: Database se user fetch karo
    repository = UserRepository(db)
    user = await repository.get_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Step 5: Inactive user ko access mat do
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_version = payload.get("token_version")
    if(
        not isinstance(token_version,int)
        or token_version != user.token_version
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Or Revoked Access Token",
            headers={"WWW-Authenticate":"Bearer"}
        )

    return user


def require_roles(*allowed_roles: str):
    async def role_checker(
        current_user=Depends(get_current_user),
    ):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )

        return current_user

    return role_checker


def require_permission(permission: Permission):
    async def permission_checker(
        current_user=Depends(get_current_user),
    ):
        if not has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )

        return current_user

    return permission_checker