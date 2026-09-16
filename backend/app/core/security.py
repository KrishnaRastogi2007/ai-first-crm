"""
Authentication/security related things.

Example:

JWT
password hashing
token validation

"""

from fastapi.concurrency import run_in_threadpool
from pwdlib import PasswordHash, exceptions
from datetime import timedelta , timezone , datetime
import jwt
from app.core.config import settings

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60

# Global instance (Sirf ek baar banega)
password_hash = PasswordHash.recommended()

# 1. Pehle normal inner functions banayein
def _hash_password_sync(password: str) -> str:
    return password_hash.hash(password)

def _verify_password_sync(password: str, password_hash_value: str) -> bool:
    try:
        return password_hash.verify(password, password_hash_value)
    except exceptions.UnknownHashError:
        return False

# 2. Ab production ke liye Async wrappers banayein (Inhe aap routes me use karenge)
async def hash_password(password: str) -> str:
    # run_in_threadpool is heavy task ko alag thread me bhej dega
    return await run_in_threadpool(_hash_password_sync, password)

async def verify_password(password: str, password_hash_value: str) -> bool:
    # Yeh login route ko block hone se bachayega
    return await run_in_threadpool(_verify_password_sync, password, password_hash_value)

# JWT SETINGS
def create_access_token(user_id: int) -> str:

    now = datetime.now(timezone.utc)

    expire_time = now + timedelta(
        minutes=JWT_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int(expire_time.timestamp())
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )

    return token

def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        return payload

    except jwt.InvalidTokenError:
        return None