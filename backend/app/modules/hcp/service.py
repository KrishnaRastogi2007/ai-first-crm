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

    async def update_hcp(self, hcp_id: int, hcp_data: HCPCreate):
        hcp = await self.repository.get_by_id(hcp_id)

        if hcp is None:
            return None

        hcp.name = hcp_data.name
        hcp.specialty = hcp_data.specialty
        hcp.email = hcp_data.email
        hcp.phone = hcp_data.phone
        hcp.organization = hcp_data.organization

        return await self.repository.update(hcp)

    async def delete_hcp(self, hcp_id: int, current_user):
        # Admin aur sales manager kisi bhi HCP ko delete kar sakte hain.
        if current_user.role in {"admin", "sales_manager"}:
            hcp = await self.repository.get_by_id(hcp_id)

            if hcp is None:
                return None

            await self.repository.delete(hcp)
            return True

        # Field representative sirf apna assigned HCP delete kar sakta hai.
        if current_user.role == "field_representative":
            deleted = await self.repository.delete_if_assigned_to(
                hcp_id=hcp_id,
                user_id=current_user.id,
            )

            if deleted:
                return True

            # Delete fail hua: HCP exist karta hai ya nahi, check karo.
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
        # Step 1: HCP exist karta hai ya nahi.
        hcp = await self.repository.get_by_id(hcp_id)

        if hcp is None:
            return None

        # Step 2: None ka matlab HCP unassign karna hai.
        if assigned_to is None:
            return await self.repository.assign_hcp(
                hcp=hcp,
                assigned_to=None,
            )

        # Step 3: Target user ko database se fetch karo.
        user = await self.user_repository.get_by_id(assigned_to)

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="Target user not found.",
            )

        # Step 4: Inactive user ko assignment mat do.
        if not user.is_active:
            raise HTTPException(
                status_code=400,
                detail="Cannot assign HCP to an inactive user.",
            )

        # Step 5: Sirf field representative ko assign karo.
        if user.role != "field_representative":
            raise HTTPException(
                status_code=400,
                detail="HCP can only be assigned to a field representative.",
            )

        # Step 6: Valid assignment database mein save karo.
        return await self.repository.assign_hcp(
            hcp=hcp,
            assigned_to=user.id,
        )
