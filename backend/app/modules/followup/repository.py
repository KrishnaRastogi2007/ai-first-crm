from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.followup.models import FollowUp


class FollowUpRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self):
        result = await self.db.execute(
            select(FollowUp)
        )
        return result.scalars().all()

    async def get_by_id(self, followup_id: int):
        result = await self.db.execute(
            select(FollowUp).where(
                FollowUp.id == followup_id
            )
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