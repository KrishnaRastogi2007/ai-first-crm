
from datetime import datetime, timezone

from ua_parser import parse

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.modules.auth.models import UserSession, Users
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import UserCreate, UserRole


def get_device_name(
    user_agent: str | None,
    sec_ch_ua: str | None = None,
) -> str | None:
    if not user_agent:
        return None

    result = parse(user_agent[:500])

    browser = (
        result.user_agent.family
        if result.user_agent
        else "Unknown Browser"
    )

    operating_system = (
        result.os.family
        if result.os
        else "Unknown OS"
    )

    # Client Hints se available browser brands parse karo.
    if sec_ch_ua:
        brands = [
            part.split(";")[0].strip().strip('"')
            for part in sec_ch_ua.split(",")
            if part.strip()
        ]

        detected_brands = [
            brand
            for brand in brands
            if brand and not brand.lower().startswith("not")
        ]

        if detected_brands:
            browser = detected_brands[0]

    return f"{browser} on {operating_system}"


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_all_users(self, page: int, limit: int):
        offset = (page - 1) * limit

        items, total = await self.repository.get_all(
            limit=limit,
            offset=offset,
        )

        pages = (total + limit - 1) // limit

        return {
            "items": items,
            "page": page,
            "limit": limit,
            "total": total,
            "pages": pages,
        }

    async def get_user_by_id(self, user_id: int):
        return await self.repository.get_by_id(user_id)

    async def create_user(self, user_data: UserCreate):
        existing_user = await self.repository.get_by_email(
            user_data.email
        )

        if existing_user is not None:
            return None

        hashed_password = await hash_password(user_data.password)

        user = Users(
            name=user_data.name,
            email=user_data.email,
            password_hash=hashed_password,
            role="field_representative",
            phone=user_data.phone,
        )

        return await self.repository.create(user)

    async def login_user(
        self,
        email: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        sec_ch_ua: str | None = None,
    ):
        user = await self.repository.get_by_email(email)

        if user is None:
            return None

        password_valid = await verify_password(
            password,
            user.password_hash,
        )

        if not password_valid or not user.is_active:
            return None

        access_token = create_access_token(
            user.id,
            token_version=user.token_version,
        )
        refresh_token = create_refresh_token(user.id)

        payload = decode_refresh_token(refresh_token)

        if payload is None:
            raise RuntimeError(
                "Failed to decode newly created refresh token"
            )

        expires_at = datetime.fromtimestamp(
            payload["exp"],
            tz=timezone.utc,
        )

        user_session = UserSession(
            user_id=user.id,
            refresh_token_jti=payload["jti"],
            ip_address=ip_address,
            user_agent=user_agent,
            device_name=get_device_name(
                user_agent,
                sec_ch_ua,
            ),
            expires_at=expires_at,
        )

        await self.repository.create_session(user_session)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def refresh_user_session(self, refresh_token: str):
        payload = decode_refresh_token(refresh_token)

        if payload is None:
            return None

        jti = payload.get("jti")
        subject = payload.get("sub")

        if not jti or not subject:
            return None

        try:
            user_id = int(subject)
        except (TypeError, ValueError):
            return None

        session = await self.repository.get_session_by_jti(jti)

        if session is None:
            return None

        now = datetime.now(timezone.utc)

        if (
            session.user_id != user_id
            or session.revoked_at is not None
            or session.expires_at <= now
        ):
            return None

        user = await self.repository.get_by_id(user_id)

        if user is None or not user.is_active:
            return None

        new_access_token = create_access_token(
            user.id,
            token_version=user.token_version,
        )
        new_refresh_token = create_refresh_token(user.id)

        new_payload = decode_refresh_token(new_refresh_token)

        if new_payload is None:
            raise RuntimeError(
                "Failed to decode newly created refresh token"
            )

        new_expires_at = datetime.fromtimestamp(
            new_payload["exp"],
            tz=timezone.utc,
        )

        new_session = UserSession(
            user_id=user.id,
            refresh_token_jti=new_payload["jti"],
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            device_name=session.device_name,
            expires_at=new_expires_at,
        )

        rotated = await self.repository.rotate_session(
            old_jti=jti,
            user_id=user.id,
            new_session=new_session,
        )

        if not rotated:
            return None

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    async def update_user_role(
        self,
        user_id: int,
        role: UserRole,
    ):
        user = await self.repository.get_by_id(user_id)

        if user is None:
            return None

        if user.role == "admin" and role.value != "admin":
            active_admins = (
                await self.repository.count_active_admins()
            )

            if active_admins <= 1:
                raise ValueError(
                    "Cannot remove the last active admin"
                )

        user.role = role.value

        await self.repository.db.commit()
        await self.repository.db.refresh(user)

        return user

    async def update_user_data(
        self,
        user_id: int,
        update_data: dict,
    ):
        user = await self.repository.get_by_id(user_id)

        if user is None:
            return None

        return await self.repository.update_user(
            user,
            update_data,
        )

    async def change_password(
        self,
        user: Users,
        current_password: str,
        new_password: str,
    ) -> bool:
        password_valid = await verify_password(
            current_password,
            user.password_hash,
        )

        if not password_valid:
            return False

        new_password_hash = await hash_password(new_password)

        await self.repository.update_password_and_revoke_sessions(
            user=user,
            password_hash=new_password_hash,
        )

        return True

    async def logout_user_session(
        self,
        refresh_token: str,
    ) -> bool:
        payload = decode_refresh_token(refresh_token)

        if payload is None:
            return False

        jti = payload.get("jti")
        subject = payload.get("sub")

        if not jti or not subject:
            return False

        try:
            user_id = int(subject)
        except (TypeError, ValueError):
            return False

        session = await self.repository.get_session_by_jti(jti)

        if session is None or session.user_id != user_id:
            return False

        if session.revoked_at is not None:
            return True

        now = datetime.now(timezone.utc)

        if session.expires_at <= now:
            return False

        await self.repository.revoke_session(session)

        return True