"""
Service actual business rules rakhti hai.

Example:

API
 ↓
Service
 ↓
Repository
 ↓
PostgreSQL

Interaction Service decide karegi:

HCP/User related checks
        ↓
Interaction valid?
        ↓
Create / Update / Delete
        ↓
Repository ko call
"""

from app.modules.interaction.repository import InteractionRepository
from app.modules.interaction.models import Interaction
from app.modules.interaction.schemas import InteractionCreate


class InteractionService:

    def __init__(self, repository: InteractionRepository):
        self.repository = repository

    async def get_all_interactions(self):
        return await self.repository.get_all()

    async def get_interaction_by_id(self, interaction_id: int):
        return await self.repository.get_by_id(interaction_id)

    async def create_interaction(
        self,
        interaction_data: InteractionCreate,
        user_id: int
    ):
        interaction = Interaction(
            hcp_id=interaction_data.hcp_id,
            user_id=user_id,
            interaction_type=interaction_data.interaction_type,
            subject=interaction_data.subject,
            notes=interaction_data.notes,
            interaction_date=interaction_data.interaction_date
        )

        return await self.repository.create(interaction)

    async def update_interaction(
        self,
        interaction_id: int,
        interaction_data: InteractionCreate,
        user_id: int
    ):
        interaction = await self.repository.get_by_id(interaction_id)

        if interaction is None:
            return None

        if interaction.user_id != user_id:
            raise PermissionError(
                "You do not have permission to update this interaction"
            )

        interaction.hcp_id = interaction_data.hcp_id
        interaction.interaction_type = interaction_data.interaction_type
        interaction.subject = interaction_data.subject
        interaction.notes = interaction_data.notes
        interaction.interaction_date = interaction_data.interaction_date

        return await self.repository.update(interaction)

    async def delete_interaction(self, interaction_id: int):

        interaction = await self.repository.get_by_id(interaction_id)

        if interaction is None:
            return None

        await self.repository.delete(interaction)

        return True