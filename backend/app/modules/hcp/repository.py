"""
Repository ka kaam:

Database se baat karna.

Example:

service.py
     ↓
repository.py
     ↓
PostgreSQL

Repository:

get_hcp()
create_hcp()
update_hcp()
delete_hcp()

Memory:

Repository = Database worker

"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.hcp.models import HCP


class HCPRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self):
        result = await self.db.execute(
            select(HCP)
        )

        return result.scalars().all()

    async def create(self, hcp: HCP):
        self.db.add(hcp)

        await self.db.commit()

        await self.db.refresh(hcp)

        return hcp
    async def update(self, hcp: HCP):
     await self.db.commit()

     await self.db.refresh(hcp)

     return hcp

    async def delete(self, hcp: HCP):
     await self.db.delete(hcp)

     await self.db.commit()

     return True
    async def get_by_id(self,hcp_id:int):
        result = await self.db.execute(
            select(HCP).where(HCP.id == hcp_id)
        )
        return result.scalar_one_or_none()