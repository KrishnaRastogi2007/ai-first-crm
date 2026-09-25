from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_user_service,get_current_user,require_permission
from app.modules.auth.service import UserService
from app.modules.auth.schemas import UserResponse
from app.core.authorization import Permission


router = APIRouter()


@router.get("/users",response_model=list[UserResponse])
async def get_users(
    service: UserService = Depends(get_user_service),
    current_user = Depends(require_permission(Permission.USERS_READ))
):
    return await service.get_all_users()


@router.get("/users/me", response_model=UserResponse)
async def get_my_profile(current_user = Depends(get_current_user)):
    return current_user


@router.get("/users/{id}",response_model=UserResponse)
async def get_user(
    id: int,service: UserService = Depends(get_user_service),
    current_user = Depends(require_permission(Permission.USERS_READ))
):
    user = await service.get_user_by_id(id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User Not Found"
        )

    return user