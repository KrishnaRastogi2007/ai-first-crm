
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from fastapi.concurrency import run_in_threadpool
from pwdlib import PasswordHash, exceptions

from app.core.config import settings

JWT_ALGORITHM = "HS256"

# Ek global password-hashing instance
password_hash = PasswordHash.recommended()


# Password hashing
def _hash_password_sync(password: str) -> str:
    return password_hash.hash(password)


def _verify_password_sync(
    password: str,
    password_hash_value: str,
) -> bool:
    try:
        return password_hash.verify(
            password,
            password_hash_value,
        )
    except exceptions.UnknownHashError:
        return False


# Async wrappers: synchronous hashing ko thread pool mein chalana
async def hash_password(password: str) -> str:
    return await run_in_threadpool(
        _hash_password_sync,
        password,
    )


async def verify_password(
    password: str,
    password_hash_value: str,
) -> bool:
    return await run_in_threadpool(
        _verify_password_sync,
        password,
        password_hash_value,
    )


# Create access token
def create_access_token(
    user_id: int,
    token_version: int,
) -> str:
    now = datetime.now(timezone.utc)

    expire_time = now + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "type": "access",
        "jti": str(uuid4()),
        "token_version": token_version,
        "iat": int(now.timestamp()),
        "exp": int(expire_time.timestamp()),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


# Decode and validate access token
def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        if payload.get("type") != "access":
            return None

        if not payload.get("sub") or not payload.get("jti"):
            return None

        token_version = payload.get("token_version")

        if (
            not isinstance(token_version, int)
            or isinstance(token_version, bool)
            or token_version < 0
        ):
            return None

        return payload

    except jwt.InvalidTokenError:
        return None


# Create refresh token
def create_refresh_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)

    expire_time = now + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )

    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": str(uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expire_time.timestamp()),
    }

    return jwt.encode(
        payload,
        settings.JWT_REFRESH_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


# Decode and validate refresh token
def decode_refresh_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_REFRESH_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        if payload.get("type") != "refresh":
            return None

        if not payload.get("sub") or not payload.get("jti"):
            return None

        return payload

    except jwt.InvalidTokenError:
        return None