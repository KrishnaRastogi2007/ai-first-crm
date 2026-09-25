from fastapi import APIRouter , Depends , HTTPException

from app.core.dependencies import get_hcp_service,get_current_user,require_permission
from app.modules.hcp.service import HCPService
from app.modules.hcp.schemas import HCPCreate , HCPResponse
from app.core.authorization import Permission

router = APIRouter()

@router.get("/hcps")
async def get_hcps(
    service: HCPService = Depends(get_hcp_service),
    current_user = Depends(require_permission(Permission.HCP_READ))
):
    return await service.get_all_hcps()

@router.get("/hcps/{id}")
async def get_hcp(
    id: int,service: HCPService = Depends(get_hcp_service),
    current_user = Depends(require_permission(Permission.HCP_READ))
):
    return await service.get_hcp_by_id(id)

@router.put("/hcps/{id}", response_model=HCPResponse)
async def update_hcp(
    id: int,
    hcp_data: HCPCreate,
    service: HCPService = Depends(get_hcp_service),
    current_user = Depends(require_permission(Permission.HCP_UPDATE))
):
    hcp = await service.update_hcp(id, hcp_data)

    if hcp is None:
        return {"detail": "HCP Not Found"}

    return hcp

@router.post("/hcp" , response_model=HCPResponse)
async def create_hcp(
    hcp_data:HCPCreate,
    service:HCPService = Depends(get_hcp_service),
    current_user = Depends(require_permission(Permission.HCP_CREATE))
):
    return await service.create_hcp(hcp_data)


@router.delete("/hcps/{id}")
async def delete_hcp(
    id: int,
    service: HCPService = Depends(get_hcp_service),
     current_user = Depends(require_permission(Permission.HCP_DELETE))
):
    hcp = await service.delete_hcp(id)

    if hcp is None:
        raise HTTPException(
            status_code=404,
            detail="HCP Not Found"
        )

    return {"message": "HCP Deleted Successfully"}