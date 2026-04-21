from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.security import verify_api_key
from app.models.orchestration_models import FleetSummaryResponse, FleetSyncRequest, FleetSyncResponse
from app.services.fleet_service import fleet_service
from app.services.watchdog_service import watchdog_service


router = APIRouter(prefix="/scale", tags=["scale"], dependencies=[Depends(verify_api_key)])


@router.post("/batches", response_model=FleetSyncResponse)
def build_batches(request: FleetSyncRequest) -> FleetSyncResponse:
    return fleet_service.build_batches(request.agent_ids, request.batch_size, request.shard_key)


@router.post("/summary", response_model=FleetSummaryResponse)
def scale_summary(request: FleetSyncRequest) -> FleetSummaryResponse:
    return fleet_service.fleet_summary(request.agent_ids)


@router.post("/recover")
def scale_recover(request: FleetSyncRequest) -> dict:
    limited = request.agent_ids[: settings.max_scale_recover_agents]
    return {
        "requested": len(request.agent_ids),
        "processed": len(limited),
        "results": watchdog_service.scan_and_recover(limited),
    }
