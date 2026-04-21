from fastapi import APIRouter, Depends

from app.core.security import verify_api_key
from app.models.dashboard_models import AgentFilterResult, DashboardCountsResponse, ShardAssignmentResponse
from app.services.dashboard_service import dashboard_service
from app.services.world_profile_service import world_profile_service
from app.services.world_profile_validator import world_profile_validator


router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(verify_api_key)])


@router.post("/counts", response_model=DashboardCountsResponse)
def counts(agent_ids: list[str]) -> DashboardCountsResponse:
    return dashboard_service.counts(agent_ids)


@router.post("/filter", response_model=AgentFilterResult)
def filter_agents(agent_ids: list[str], require_tasks: bool = False, require_learning: bool = False) -> AgentFilterResult:
    return dashboard_service.filter_agents(agent_ids, require_tasks=require_tasks, require_learning=require_learning)


@router.post("/shards", response_model=list[ShardAssignmentResponse])
def shard_assign(agent_ids: list[str], shard_count: int = 1) -> list[ShardAssignmentResponse]:
    return dashboard_service.shard_assign(agent_ids, shard_count)


@router.get("/world-profile/{world_id}")
def validate_world_profile(world_id: str) -> dict:
    profile = world_profile_service.load(world_id)
    validation = world_profile_validator.validate(profile)
    return {"world_id": world_id, "validation": validation, "profile": profile}
