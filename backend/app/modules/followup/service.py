from app.modules.followup.models import FollowUp
from app.modules.followup.repository import FollowUpRepository
from app.modules.followup.schemas import FollowUpCreate


class FollowUpService:

    def __init__(self, repository: FollowUpRepository):
        self.repository = repository

    async def get_all_followups(self):
        return await self.repository.get_all()

    async def get_followup_by_id(self, followup_id: int):
        return await self.repository.get_by_id(followup_id)

    async def create_followup(self, followup_data: FollowUpCreate):

        followup = FollowUp(
            interaction_id=followup_data.interaction_id,
            assigned_to=followup_data.assigned_to,
            due_date=followup_data.due_date,
            status=followup_data.status,
            notes=followup_data.notes
        )

        return await self.repository.create(followup)

    async def update_followup(
        self,
        followup_id: int,
        followup_data: FollowUpCreate
    ):

        followup = await self.repository.get_by_id(
            followup_id
        )

        if followup is None:
            return None

        followup.interaction_id = followup_data.interaction_id
        followup.assigned_to = followup_data.assigned_to
        followup.due_date = followup_data.due_date
        followup.status = followup_data.status
        followup.notes = followup_data.notes

        return await self.repository.update(followup)

    async def delete_followup(self, followup_id: int):

        followup = await self.repository.get_by_id(
            followup_id
        )

        if followup is None:
            return None

        await self.repository.delete(followup)

        return True