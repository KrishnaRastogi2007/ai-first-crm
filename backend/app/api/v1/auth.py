from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_user_service

from app.modules.auth.service import UserService

from app.modules.auth.schemas import UserCreate,UserResponse


router = APIRouter()

@router.post("/auth/register",response_model=UserResponse)
async def register_user(user_data: UserCreate,service: UserService = Depends(get_user_service)):
    user = await service.create_user(user_data)

    if user is None:
        raise HTTPException(
            status_code=409,
            detail="User With This Email Already Exists"
        )

    return user