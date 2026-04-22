from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse

from app.core.security import verify_api_key
from app.models.dashboard_models import (
    AgentFilterResult,
    DashboardCountsResponse,
    RobotAiOpsDashboardResponse,
    ShardAssignmentResponse,
)
from app.services.dashboard_service import dashboard_service
from app.services.rebalance_service import rebalance_service
from app.services.robot_ai_ops_service import robot_ai_ops_service
from app.services.shard_balancer_service import shard_balancer_service
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


@router.post("/shards-weighted")
def shard_assign_weighted(agent_ids: list[str], shard_count: int = 1) -> list[dict]:
    return shard_balancer_service.weighted_assign(agent_ids, shard_count)


@router.post("/rebalance")
def shard_rebalance(agent_ids: list[str], shard_count: int = 1) -> dict:
    shards = shard_balancer_service.weighted_assign(agent_ids, shard_count)
    recommendation = rebalance_service.recommend(shards)
    return {
        "shards": shards,
        "recommendation": recommendation,
    }


@router.get("/world-profile/{world_id}")
def validate_world_profile(world_id: str) -> dict:
    profile = world_profile_service.load(world_id)
    validation = world_profile_validator.validate(profile)
    return {"world_id": world_id, "validation": validation, "profile": profile}


@router.get("/robot-ai", response_model=RobotAiOpsDashboardResponse)
def robot_ai_dashboard(agent_ids: list[str] = Query(default=[])) -> RobotAiOpsDashboardResponse:
    return robot_ai_ops_service.dashboard_snapshot(agent_ids)


@router.get("/robot-ai/gui", response_class=HTMLResponse)
def robot_ai_dashboard_gui(agent_ids: list[str] = Query(default=[])) -> HTMLResponse:
    return HTMLResponse(robot_ai_ops_service.render_dashboard_html(agent_ids))
