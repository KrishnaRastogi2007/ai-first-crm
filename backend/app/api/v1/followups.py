from fastapi import APIRouter, Depends, HTTPException,Query
from app.core.authorization import Permission
from app.core.dependencies import get_followup_service,require_permission
from app.modules.followup.schemas import FollowUpCreate, FollowUpResponse,PaginatedFollowupResponse
from app.modules.followup.service import FollowUpService

router = APIRouter()


@router.get("/followups", response_model=PaginatedFollowupResponse)
async def get_followups(
    page:int = Query(1,ge=1),
    limit:int = Query(20,ge=1,le=50),
    service: FollowUpService = Depends(get_followup_service),
    current_user=Depends(require_permission(Permission.FOLLOWUP_READ)),
):
    return await service.get_all_followups(page,limit)


@router.get("/followups/{id}", response_model=FollowUpResponse)
async def get_followup(
    id: int,
    service: FollowUpService = Depends(get_followup_service),
    current_user=Depends(require_permission(Permission.FOLLOWUP_READ)),
):

    followup = await service.get_followup_by_id(id)

    if followup is None:
        raise HTTPException(status_code=404, detail="FollowUp Not Found")

    return followup


@router.post("/followups", response_model=FollowUpResponse)
async def create_followup(
    followup_data: FollowUpCreate,
    service: FollowUpService = Depends(get_followup_service),
    current_user=Depends(require_permission(Permission.FOLLOWUP_CREATE)),
):

    return await service.create_followup(followup_data)


@router.put("/followups/{id}", response_model=FollowUpResponse)
async def update_followup(
    id: int,
    followup_data: FollowUpCreate,
    service: FollowUpService = Depends(get_followup_service),
    current_user=Depends(require_permission(Permission.FOLLOWUP_UPDATE)),
):

    followup = await service.update_followup(id, followup_data)

    if followup is None:
        raise HTTPException(status_code=404, detail="FollowUp Not Found")

    return followup


@router.delete("/followups/{id}")
async def delete_followup(
    id: int,
    service: FollowUpService = Depends(get_followup_service),
    current_user=Depends(require_permission(Permission.FOLLOWUP_DELETE)),
):

    followup = await service.delete_followup(id)

    if followup is None:
        raise HTTPException(status_code=404, detail="FollowUp Not Found")

    return {"message": "FollowUp Deleted Successfully"}
