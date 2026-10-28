
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.authorization import Permission
from app.core.dependencies import get_hcp_service, require_permission
from app.modules.hcp.schemas import (
    HCPCreate,
    HCPResponse,
    PaginatedHCPResponse,
    HCPAssignment,
)
from app.modules.hcp.service import HCPService


router = APIRouter()


@router.get("/hcps", response_model=PaginatedHCPResponse)
async def get_hcps(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    name: str | None = Query(None, min_length=1, max_length=100),
    specialty: str | None = Query(None, min_length=1, max_length=150),
    keyword: str | None = Query(None, min_length=1, max_length=100),
    email: str | None = Query(None, min_length=1, max_length=254),
    organization: str | None = Query(None, min_length=1, max_length=200),
    email_exact: bool = Query(False),
    organization_exact: bool = Query(False),
    service: HCPService = Depends(get_hcp_service),
    current_user=Depends(require_permission(Permission.HCP_READ)),
):
    return await service.search_hcps(
        page=page,
        limit=limit,
        name=name,
        specialty=specialty,
        keyword=keyword,
        email=email,
        organization=organization,
        email_exact=email_exact,
        organization_exact=organization_exact,
    )


@router.get("/hcps/{id}", response_model=HCPResponse)
async def get_hcp(
    id: int,
    service: HCPService = Depends(get_hcp_service),
    current_user=Depends(require_permission(Permission.HCP_READ)),
):
    hcp = await service.get_hcp_by_id(id)

    if hcp is None:
        raise HTTPException(
            status_code=404,
            detail="HCP Not Found",
        )

    return hcp


@router.put("/hcps/{id}", response_model=HCPResponse)
async def update_hcp(
    id: int,
    hcp_data: HCPCreate,
    service: HCPService = Depends(get_hcp_service),
    current_user=Depends(require_permission(Permission.HCP_UPDATE)),
):
    hcp = await service.update_hcp(
        hcp_id=id,
        hcp_data=hcp_data,
        current_user=current_user
    )

    if hcp is None:
        raise HTTPException(
            status_code=404,
            detail="HCP Not Found",
        )

    return hcp


@router.post("/hcps", response_model=HCPResponse)
async def create_hcp(
    hcp_data: HCPCreate,
    service: HCPService = Depends(get_hcp_service),
    current_user=Depends(require_permission(Permission.HCP_CREATE)),
):
    return await service.create_hcp(hcp_data)


@router.delete("/hcps/{id}")
async def delete_hcp(
    id: int,
    service: HCPService = Depends(get_hcp_service),
    current_user=Depends(require_permission(Permission.HCP_DELETE)),
):
    hcp = await service.delete_hcp(
        hcp_id=id,
        current_user=current_user,
    )

    if hcp is None:
        raise HTTPException(
            status_code=404,
            detail="HCP Not Found",
        )

    return {"message": "HCP Deleted Successfully"}


@router.patch("/hcps/{id}/assignment", response_model=HCPResponse)
async def assign_hcp(
    id: int,
    assignment_data: HCPAssignment,
    service: HCPService = Depends(get_hcp_service),
    current_user=Depends(
        require_permission(Permission.HCP_ASSIGN)
    ),
):
    hcp = await service.assign_hcp(
        hcp_id=id,
        assigned_to=assignment_data.assigned_to,
    )

    if hcp is None:
        raise HTTPException(
            status_code=404,
            detail="HCP Not Found",
        )

    return hcp
