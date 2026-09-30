from fastapi import APIRouter, Depends, HTTPException,Query
from app.core.authorization import Permission
from app.core.dependencies import get_current_user, get_user_service, require_permission
from app.modules.auth.schemas import UserResponse,PaginatedUserResponse
from app.modules.auth.service import UserService

router = APIRouter()


@router.get("/users", response_model=PaginatedUserResponse)
async def get_users(
    page:int = Query(1,ge=1),
    limit:int = Query(20,ge=1,le=50),
    service: UserService = Depends(get_user_service),
    current_user=Depends(require_permission(Permission.USERS_READ)),
):
    return await service.get_all_users(page,limit)


@router.get("/users/me", response_model=UserResponse)
async def get_my_profile(current_user=Depends(get_current_user)):
    return current_user


@router.get("/users/{id}", response_model=UserResponse)
async def get_user(
    id: int,
    service: UserService = Depends(get_user_service),
    current_user=Depends(require_permission(Permission.USERS_READ)),
):
    user = await service.get_user_by_id(id)

    if user is None:
        raise HTTPException(status_code=404, detail="User Not Found")

    return user
