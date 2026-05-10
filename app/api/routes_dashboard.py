from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse

from app.core.security import verify_api_key
from app.models.dash import (
    AgentFilterResult,
    DashboardCountsResponse,
    RobotAiOpsDashboardResponse,
    ShardAssignmentResponse,
)
from app.services.autonomy import robot_autonomy_baseline_service
from app.services.dashboard_service import dashboard_service
from app.services.rebalance_service import rebalance_service
from app.services.robot_ai_ops_service import robot_ai_ops_service
from app.services.server_context_service import server_context_service
from app.services.shard_balancer_service import shard_balancer_service
from app.services.spawn_dash import spawn_request_dashboard_service
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
    return {"shards": shards, "recommendation": recommendation}


@router.get("/world-profile/{world_id}")
def validate_world_profile(world_id: str) -> dict:
    profile = world_profile_service.load(world_id)
    validation = world_profile_validator.validate(profile)
    return {"world_id": world_id, "validation": validation, "profile": profile}


@router.get("/server-context")
def server_context() -> dict:
    return server_context_service.snapshot()


@router.get("/robot-ai", response_model=RobotAiOpsDashboardResponse)
def robot_ai_dashboard(agent_ids: list[str] = Query(default=[])) -> RobotAiOpsDashboardResponse:
    return robot_ai_ops_service.dashboard_snapshot(agent_ids)


@router.get("/robot-ai/gui", response_class=HTMLResponse)
def robot_ai_dashboard_gui(agent_ids: list[str] = Query(default=[])) -> HTMLResponse:
    return HTMLResponse(robot_ai_ops_service.render_dashboard_html(agent_ids))


@router.get("/robot-spawn-queue")
def robot_spawn_queue(
    limit: int = Query(default=30, ge=1, le=200),
    status: str | None = Query(default=None),
    server_name: str | None = Query(default=None),
) -> dict:
    return spawn_request_dashboard_service.summary(limit, status, server_name)


@router.get("/robot-spawn-queue/gui", response_class=HTMLResponse)
def robot_spawn_queue_gui(
    limit: int = Query(default=30, ge=1, le=200),
    status: str | None = Query(default=None),
    server_name: str | None = Query(default=None),
) -> HTMLResponse:
    return HTMLResponse(spawn_request_dashboard_service.render_html(limit, status, server_name))


@router.post("/robot-spawn-queue/retry-failed")
def retry_failed_spawn_requests(
    server_name: str = Query(default="main"),
    limit: int = Query(default=50, ge=1, le=500),
) -> dict:
    return spawn_request_dashboard_service.retry_failed(server_name=server_name, limit=limit)


@router.post("/robot-spawn-queue/recover-claimed")
def recover_claimed_spawn_requests(
    server_name: str = Query(default="main"),
    older_than_minutes: int = Query(default=10, ge=1, le=1440),
    limit: int = Query(default=50, ge=1, le=500),
) -> dict:
    return spawn_request_dashboard_service.recover_stale_claimed(server_name=server_name, older_than_minutes=older_than_minutes, limit=limit)


@router.get("/robot-autonomy-baseline")
def robot_autonomy_baseline() -> dict:
    return robot_autonomy_baseline_service.operator_view()


@router.post("/robot-autonomy-baseline")
def save_robot_autonomy_baseline(config: dict) -> dict:
    saved = robot_autonomy_baseline_service.save_operator_config(config)
    return {"accepted": True, "config_path": str(robot_autonomy_baseline_service.config_path), "config": saved}


@router.post("/robot-autonomy-baseline/reload")
def reload_robot_autonomy_baseline() -> dict:
    return {"accepted": True, "baseline": robot_autonomy_baseline_service.load(force=True)}
