from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import Users, UserSession


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, limit: int, offset: int):
        result = await self.db.execute(
            select(Users)
            .order_by(Users.id)
            .offset(offset)
            .limit(limit)
        )

        items = result.scalars().all()

        count_result = await self.db.execute(
            select(func.count()).select_from(Users)
        )

        total = count_result.scalar_one()

        return items, total

    async def get_by_id(self, user_id: int) -> Users | None:
        result = await self.db.execute(
            select(Users).where(Users.id == user_id)
        )

        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Users | None:
        result = await self.db.execute(
            select(Users).where(Users.email == email)
        )

        return result.scalar_one_or_none()

    async def count_active_admins(self) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Users)
            .where(
                Users.role == "admin",
                Users.is_active.is_(True),
            )
        )

        return result.scalar_one()

    async def create(self, user: Users) -> Users:
        try:
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user

        except Exception:
            await self.db.rollback()
            raise

    async def update_user(
        self,
        user: Users,
        update_data: dict,
    ) -> Users:
        try:
            for field, value in update_data.items():
                setattr(user, field, value)

            await self.db.commit()
            await self.db.refresh(user)
            return user

        except Exception:
            await self.db.rollback()
            raise

    async def update_password(
        self,
        user: Users,
        password_hash: str,
    ) -> Users:
        try:
            user.password_hash = password_hash

            await self.db.commit()
            await self.db.refresh(user)
            return user

        except Exception:
            await self.db.rollback()
            raise

    async def create_session(
        self,
        session: UserSession,
    ) -> UserSession:
        try:
            self.db.add(session)
            await self.db.commit()
            await self.db.refresh(session)
            return session

        except Exception:
            await self.db.rollback()
            raise

    async def get_session_by_jti(
        self,
        jti: str,
    ) -> UserSession | None:
        result = await self.db.execute(
            select(UserSession).where(
                UserSession.refresh_token_jti == jti
            )
        )

        return result.scalar_one_or_none()

    async def revoke_session(
        self,
        session: UserSession,
    ) -> UserSession:
        try:
            if session.revoked_at is not None:
                return session

            session.revoked_at = datetime.now(timezone.utc)

            await self.db.commit()
            await self.db.refresh(session)
            return session

        except Exception:
            await self.db.rollback()
            raise

    async def revoke_all_user_sessions(
        self,
        user_id: int,
    ) -> int:
        try:
            result = await self.db.execute(
                select(UserSession).where(
                    UserSession.user_id == user_id,
                    UserSession.revoked_at.is_(None),
                )
            )

            sessions = result.scalars().all()
            now = datetime.now(timezone.utc)

            for session in sessions:
                session.revoked_at = now

            await self.db.commit()
            return len(sessions)

        except Exception:
            await self.db.rollback()
            raise

    async def update_password_and_revoke_sessions(
        self,
        user: Users,
        password_hash: str,
    ) -> int:
        try:
            # 1. Password hash update karo.
            user.password_hash = password_hash

            # 2. Purane access tokens invalidate karo.
            user.token_version += 1

            # 3. Active refresh sessions fetch karo.
            result = await self.db.execute(
                select(UserSession).where(
                    UserSession.user_id == user.id,
                    UserSession.revoked_at.is_(None),
                )
            )

            sessions = result.scalars().all()
            now = datetime.now(timezone.utc)

            # 4. Saari active sessions revoke karo.
            for session in sessions:
                session.revoked_at = now

            # 5. Ek hi transaction mein save karo.
            await self.db.commit()

            return len(sessions)

        except Exception:
            await self.db.rollback()
            raise

    async def rotate_session(
        self,
        old_jti: str,
        user_id: int,
        new_session: UserSession,
    ) -> bool:
        try:
            result = await self.db.execute(
                select(UserSession)
                .where(UserSession.refresh_token_jti == old_jti)
                .with_for_update()
            )

            old_session = result.scalar_one_or_none()

            if old_session is None:
                await self.db.rollback()
                return False

            now = datetime.now(timezone.utc)

            if (
                old_session.user_id != user_id
                or old_session.revoked_at is not None
                or old_session.expires_at <= now
            ):
                await self.db.rollback()
                return False

            if new_session.user_id != user_id:
                await self.db.rollback()
                return False

            old_session.last_used_at = now
            old_session.revoked_at = now

            self.db.add(new_session)

            await self.db.commit()
            return True

        except Exception:
            await self.db.rollback()
            raise
