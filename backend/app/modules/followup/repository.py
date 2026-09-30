from sqlalchemy import select,func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.followup.models import FollowUp


class FollowUpRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self,limit:int,offset:int):
        result = await self.db.execute(
            select(FollowUp)
            .order_by(FollowUp.id)
            .offset(offset)
            .limit(limit)
        )

        items = result.scalars().all()
        count_result = await self.db.execute(
            select(func.count()).select_from(FollowUp)
        )
        total=count_result.scalar_one()
        return items,total

    async def get_by_id(self, followup_id: int):
        result = await self.db.execute(
            select(FollowUp).where(FollowUp.id == followup_id)
        )
        return result.scalar_one_or_none()

    async def create(self, followup: FollowUp):
        self.db.add(followup)

        await self.db.commit()
        await self.db.refresh(followup)

        return followup

    async def update(self, followup: FollowUp):
        await self.db.commit()
        await self.db.refresh(followup)

        return followup

    async def delete(self, followup: FollowUp):
        await self.db.delete(followup)

        await self.db.commit()

        return True
