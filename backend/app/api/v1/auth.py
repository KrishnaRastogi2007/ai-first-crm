from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_user_service

from app.modules.auth.service import UserService

from app.modules.auth.schemas import (
    UserCreate,
    UserResponse
)


router = APIRouter()


@router.get(
    "/users",
    response_model=list[UserResponse]
)
async def get_users(
    service: UserService = Depends(get_user_service)
):
    return await service.get_all_users()


@router.get(
    "/users/{id}",
    response_model=UserResponse
)
async def get_user(
    id: int,
    service: UserService = Depends(get_user_service)
):
    user = await service.get_user_by_id(id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User Not Found"
        )

    return user


@router.post(
    "/users",
    response_model=UserResponse
)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service)
):
    user = await service.create_user(user_data)

    if user is None:
        raise HTTPException(
            status_code=409,
            detail="User With This Email Already Exists"
        )

    return user