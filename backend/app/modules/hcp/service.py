"""
Service actual business rules rakhti hai.

Example:

API
 ↓
Service
 ↓
Repository
 ↓
DB

Suppose interaction log karna hai.

Service decide karegi:

HCP exists?
        ↓
Interaction valid?
        ↓
User allowed?
        ↓
Create interaction
        ↓
Create audit log
        ↓
Schedule follow-up?

Memory:

Service = decision maker
"""

from app.modules.hcp.repository import HCPRepository
from app.modules.hcp.models import HCP
from app.modules.hcp.schemas import HCPCreate


class HCPService:

    def __init__(self, repository: HCPRepository):
        self.repository = repository

    async def get_all_hcps(self):
        return await self.repository.get_all()
    async def get_hcp_by_id(self,hcp_id:int):
        return await self.repository.get_by_id(hcp_id)

    async def create_hcp(self,hcp_data:HCPCreate):
        hcp = HCP(
            name = hcp_data.name,
            specialty = hcp_data.specialty,
            email = hcp_data.email,
            phone = hcp_data.phone,
            organization = hcp_data.organization

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
