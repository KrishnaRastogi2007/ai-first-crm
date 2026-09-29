from app.modules.hcp.models import HCP
from app.modules.hcp.repository import HCPRepository
from app.modules.hcp.schemas import HCPCreate


class HCPService:
    def __init__(self, repository: HCPRepository):
        self.repository = repository

    async def get_all_hcps(self,page:int,limit:int):
        # Page --> User Requeasted Page.
        # limit --> ek page mein maximum HCPs.
        offset = (page- 1)*limit
        items,total = await self.repository.get_all(
            limit=limit, # Current Page HCPs
            offset=offset,# database mein total HCPs
        )
        pages = (total + limit - 1) // limit
        return{
            "items":items,
            "page":page,
            "limit":limit,
            "total":total,
            "pages":pages
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

    async def delete_hcp(self, hcp_id: int):

        hcp = await self.repository.get_by_id(hcp_id)

        if hcp is None:
            return None

        await self.repository.delete(hcp)

        return True
