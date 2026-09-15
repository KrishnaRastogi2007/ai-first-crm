from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_interaction_service
from app.modules.interaction.service import InteractionService
from app.modules.interaction.schemas import InteractionCreate,InteractionResponse



router = APIRouter()


@router.get("/interactions",response_model=list[InteractionResponse])
async def get_interactions(
    service: InteractionService = Depends(get_interaction_service)
):
    return await service.get_all_interactions()


@router.get("/interactions/{id}",response_model=InteractionResponse)
async def get_interaction(
    id: int,
    service: InteractionService = Depends(get_interaction_service)
):
    interaction = await service.get_interaction_by_id(id)

    if interaction is None:
        raise HTTPException(
            status_code=404,
            detail="Interaction Not Found"
        )

    return interaction


@router.post("/interactions",response_model=InteractionResponse)
async def create_interaction(
    interaction_data: InteractionCreate,
    service: InteractionService = Depends(get_interaction_service)
):
    return await service.create_interaction(interaction_data)


@router.put("/interactions/{id}",response_model=InteractionResponse)
async def update_interaction(
    id: int,
    interaction_data: InteractionCreate,
    service: InteractionService = Depends(get_interaction_service)
):
    interaction = await service.update_interaction(
        id,
        interaction_data
    )

    if interaction is None:
        raise HTTPException(
            status_code=404,
            detail="Interaction Not Found"
        )

    return interaction


@router.delete("/interactions/{id}")
async def delete_interaction(
    id: int,
    service: InteractionService = Depends(get_interaction_service)
):
    interaction = await service.delete_interaction(id)

    if interaction is None:
        raise HTTPException(
            status_code=404,
            detail="Interaction Not Found"
        )

    return {
        "message": "Interaction Deleted Successfully"
    }
