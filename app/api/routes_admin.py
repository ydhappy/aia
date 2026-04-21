from fastapi import APIRouter, Depends, Query

from app.core.security import verify_api_key
from app.models.admin_models import AdminRobotSummaryResponse, AdminSystemSummaryResponse, RecoveryActionResponse
from app.services.admin_service import admin_service
from app.services.recovery_service import recovery_service


router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(verify_api_key)])


@router.get("/robot/{agent_id}", response_model=AdminRobotSummaryResponse)
def robot_summary(agent_id: str) -> AdminRobotSummaryResponse:
    return admin_service.robot_summary(agent_id)


@router.get("/system", response_model=AdminSystemSummaryResponse)
def system_summary(agent_ids: list[str] = Query(default=[])) -> AdminSystemSummaryResponse:
    return admin_service.system_summary(agent_ids)


@router.post("/recover/{agent_id}", response_model=RecoveryActionResponse)
def recover_agent(agent_id: str) -> RecoveryActionResponse:
    return recovery_service.recover_agent(agent_id)
