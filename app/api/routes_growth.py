from fastapi import APIRouter, Depends

from app.core.security import verify_api_key
from app.models.growth_models import GrowthStateResponse
from app.services.growth_service import growth_service


router = APIRouter(prefix="/growth", tags=["growth"], dependencies=[Depends(verify_api_key)])


@router.get("/{agent_id}", response_model=GrowthStateResponse)
def growth_state(agent_id: str) -> GrowthStateResponse:
    return growth_service.get_growth_state(agent_id)
