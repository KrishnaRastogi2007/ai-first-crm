
from fastapi import HTTPException

from app.modules.auth.repository import UserRepository
from app.modules.hcp.models import HCP
from app.modules.hcp.repository import HCPRepository
from app.modules.hcp.schemas import HCPCreate


class HCPService:
    def __init__(
        self,
        repository: HCPRepository,
        user_repository: UserRepository,
    ):
        self.repository = repository
        self.user_repository = user_repository

    async def get_all_hcps(self, page: int, limit: int):
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

    async def search_hcps(
        self,
        page: int,
        limit: int,
        name: str | None = None,
        specialty: str | None = None,
        keyword: str | None = None,
        email: str | None = None,
        organization: str | None = None,
        email_exact: bool = False,
        organization_exact: bool = False,
    ):
        offset = (page - 1) * limit

        items, total = await self.repository.search_hcps(
            limit=limit,
            offset=offset,
            name=name,
            specialty=specialty,
            keyword=keyword,
            email=email,
            organization=organization,
            email_exact=email_exact,
            organization_exact=organization_exact,
        )

        pages = (total + limit - 1) // limit

        return {
            "items": items,
            "page": page,
            "limit": limit,
            "total": total,
            "pages": pages,
        }

    async def get_hcp_by_id(self, hcp_id: int):
        return await self.repository.get_by_id(hcp_id)

    async def create_hcp(self, hcp_data: HCPCreate):
        hcp = HCP(
            name=hcp_data.name,
            specialty=hcp_data.specialty,
            email=hcp_data.email,
            phone=hcp_data.phone,
            organization=hcp_data.organization,
        )

        return await self.repository.create(hcp)

    async def update_hcp(
        self,
        hcp_id: int,
        hcp_data: HCPCreate,
        current_user,
    ):
        hcp = await self.repository.get_by_id(hcp_id)

        if hcp is None:
            return None

        if current_user.role in {"admin", "sales_manager"}:
            # Admin aur sales manager kisi bhi HCP ko update kar sakte hain.
            pass

        elif current_user.role == "field_representative":
            # Field representative sirf assigned HCP update kar sakta hai.
            if hcp.assigned_to != current_user.id:
                raise HTTPException(
                    status_code=403,
                    detail="You can only update HCPs assigned to you.",
                )

        else:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to update HCPs.",
            )

        hcp.name = hcp_data.name
        hcp.specialty = hcp_data.specialty
        hcp.email = hcp_data.email
        hcp.phone = hcp_data.phone
        hcp.organization = hcp_data.organization

        return await self.repository.update(hcp)

    async def delete_hcp(self, hcp_id: int, current_user):
        if current_user.role in {"admin", "sales_manager"}:
            hcp = await self.repository.get_by_id(hcp_id)

            if hcp is None:
                return None

            await self.repository.delete(hcp)
            return True

        if current_user.role == "field_representative":
            deleted = await self.repository.delete_if_assigned_to(
                hcp_id=hcp_id,
                user_id=current_user.id,
            )

            if deleted:
                return True

            hcp = await self.repository.get_by_id(hcp_id)

            if hcp is None:
                return None

            raise HTTPException(
                status_code=403,
                detail="You can only delete HCPs assigned to you.",
            )

        raise HTTPException(
            status_code=403,
            detail="You do not have permission to delete HCPs.",
        )

    async def assign_hcp(
        self,
        hcp_id: int,
        assigned_to: int | None,
    ):
        hcp = await self.repository.get_by_id(hcp_id)

        if hcp is None:
            return None

        if assigned_to is None:
            return await self.repository.assign_hcp(
                hcp=hcp,
                assigned_to=None,
            )

        user = await self.user_repository.get_by_id(assigned_to)

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="Target user not found.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=400,
                detail="Cannot assign HCP to an inactive user.",
            )

        if user.role != "field_representative":
            raise HTTPException(
                status_code=400,
                detail="HCP can only be assigned to a field representative.",
            )

        return await self.repository.assign_hcp(
            hcp=hcp,
            assigned_to=user.id,
        )
