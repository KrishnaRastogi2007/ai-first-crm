
from sqlalchemy import select, func, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.hcp.models import HCP


class HCPRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, limit: int, offset: int):
        result = await self.db.execute(
            select(HCP)
            .order_by(HCP.id)
            .offset(offset)
            .limit(limit)
        )

        items = result.scalars().all()

        count_result = await self.db.execute(
            select(func.count()).select_from(HCP)
        )

        total = count_result.scalar_one()

        return items, total

    async def search_hcps(
        self,
        limit: int,
        offset: int,
        name: str | None = None,
        specialty: str | None = None,
        keyword: str | None = None,
        email: str | None = None,
        organization: str | None = None,
        email_exact: bool = False,
        organization_exact: bool = False,
    ):
        filters = []

        # Name: case-insensitive partial matching.
        if name and name.strip():
            filters.append(
                HCP.name.ilike(f"%{name.strip()}%")
            )

        # Specialty: case-insensitive partial matching.
        if specialty and specialty.strip():
            filters.append(
                HCP.specialty.ilike(f"%{specialty.strip()}%")
            )

        # Email: partial or exact matching.
        if email and email.strip():
            email_value = email.strip()

            if email_exact:
                filters.append(
                    HCP.email.ilike(email_value)
                )
            else:
                filters.append(
                    HCP.email.ilike(f"%{email_value}%")
                )

        # Organization: partial or exact matching.
        if organization and organization.strip():
            organization_value = organization.strip()

            if organization_exact:
                filters.append(
                    HCP.organization.ilike(organization_value)
                )
            else:
                filters.append(
                    HCP.organization.ilike(
                        f"%{organization_value}%"
                    )
                )

        # Keyword: search across all four fields.
        if keyword and keyword.strip():
            pattern = f"%{keyword.strip()}%"

            filters.append(
                or_(
                    HCP.name.ilike(pattern),
                    HCP.specialty.ilike(pattern),
                    HCP.organization.ilike(pattern),
                    HCP.email.ilike(pattern),
                )
            )

        # Fetch the requested page.
        query = (
            select(HCP)
            .where(*filters)
            .order_by(HCP.id)
            .offset(offset)
            .limit(limit)
        )

        result = await self.db.execute(query)
        items = result.scalars().all()

        # Count all records matching the same filters.
        count_query = (
            select(func.count())
            .select_from(HCP)
            .where(*filters)
        )

        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()

        return items, total

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

    async def delete_if_assigned_to(
        self,
        hcp_id: int,
        user_id: int,
    ) -> bool:
        statement = (
            delete(HCP)
            .where(
                HCP.id == hcp_id,
                HCP.assigned_to == user_id,
            )
            .returning(HCP.id)
        )

        result = await self.db.execute(statement)
        deleted_id = result.scalar_one_or_none()

        await self.db.commit()

        return deleted_id is not None

    async def get_by_id(self, hcp_id: int):
        result = await self.db.execute(
            select(HCP).where(HCP.id == hcp_id)
        )

        return result.scalar_one_or_none()

    async def assign_hcp(
        self,
        hcp: HCP,
        assigned_to: int | None,
    ) -> HCP:
        hcp.assigned_to = assigned_to

        await self.db.commit()
        await self.db.refresh(hcp)

        return hcp
