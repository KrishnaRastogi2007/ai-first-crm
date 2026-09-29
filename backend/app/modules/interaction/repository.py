from sqlalchemy import select , func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.interaction.models import Interaction


class InteractionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self,limit:int,offset:int):
        result = await self.db.execute(
            select(Interaction)
            .order_by(Interaction.id)
            .offset(offset)
            .limit(limit)
        )

        items = result.scalars().all()
        count_result = await self.db.execute(
            select(func.count()).select_from(Interaction)
        )
        total = count_result.scalar_one()

        return items,total

    async def get_by_id(self, interaction_id: int):
        result = await self.db.execute(
            select(Interaction).where(Interaction.id == interaction_id)
        )

        return result.scalar_one_or_none()

    async def create(self, interaction: Interaction):
        self.db.add(interaction)

        await self.db.commit()

        await self.db.refresh(interaction)

        return interaction

    async def update(self, interaction: Interaction):
        await self.db.commit()

        await self.db.refresh(interaction)

        return interaction

    async def delete(self, interaction: Interaction):
        await self.db.delete(interaction)

        await self.db.commit()

        return True
