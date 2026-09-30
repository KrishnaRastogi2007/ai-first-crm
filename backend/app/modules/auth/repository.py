from sqlalchemy import select,func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import Users


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self,limit:int,offset:int):
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

        return items,total

    async def get_by_id(self, user_id: int):
        result = await self.db.execute(select(Users).where(Users.id == user_id))

        return result.scalar_one_or_none()

    async def get_by_email(self, email: str):
        result = await self.db.execute(select(Users).where(Users.email == email))

        return result.scalar_one_or_none()

    async def create(self, user: Users):
        self.db.add(user)

        await self.db.commit()

        await self.db.refresh(user)

        return user
