from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.security import verify_api_key
from app.models.batch_models import BatchDecideRequest, BatchDecideResponse, BatchObserveRequest, BatchObserveResponse
from app.services.agent_service import agent_service


router = APIRouter(tags=["batch"])


@router.post("/observe/batch", response_model=BatchObserveResponse, dependencies=[Depends(verify_api_key)])
def observe_batch(request: BatchObserveRequest) -> BatchObserveResponse:
    if not settings.allow_batch_requests:
        return BatchObserveResponse(items=[])
    items = request.items[: settings.max_batch_size]
    return agent_service.observe_batch(items)


@router.post("/decide/batch", response_model=BatchDecideResponse, dependencies=[Depends(verify_api_key)])
def decide_batch(request: BatchDecideRequest) -> BatchDecideResponse:
    if not settings.allow_batch_requests:
        return BatchDecideResponse(items=[])
    items = request.items[: settings.max_batch_size]
    return agent_service.decide_batch(items)
