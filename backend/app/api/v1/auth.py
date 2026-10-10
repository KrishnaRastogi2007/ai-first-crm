
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import get_current_user, get_user_service
from app.modules.auth.schemas import (
    ChangePasswordRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.modules.auth.service import UserService

router = APIRouter()


@router.post("/auth/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service),
):
    user = await service.create_user(user_data)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    return user


@router.post("/auth/login", response_model=TokenResponse)
async def login_user(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_user_service),
):
    result = await service.login_user(
        email=form_data.username,
        password=form_data.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        sec_ch_ua=request.headers.get("sec-ch-ua")
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return result


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    service: UserService = Depends(get_user_service),
):
    result = await service.refresh_user_session(data.refresh_token)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or revoked refresh token",
        )

    return result


@router.post("/auth/logout")
async def logout_user(
    data: RefreshTokenRequest,
    service: UserService = Depends(get_user_service),
):
    result = await service.logout_user_session(data.refresh_token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or revoked refresh token",
        )

    return {"message": "Logged out successfully"}


@router.post("/auth/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user=Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    result = await service.change_password(
        user=current_user,
        current_password=data.current_password,
        new_password=data.new_password,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    return {"message": "Password changed successfully"}