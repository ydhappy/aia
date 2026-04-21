from fastapi import APIRouter, Depends

from app.core.security import verify_api_key
from app.models.request_models import DecideRequest, ObserveRequest
from app.models.response_models import DecideResponse, ObserveResponse
from app.services.agent_service import agent_service


router = APIRouter(tags=["agent"])


@router.post("/observe", response_model=ObserveResponse, dependencies=[Depends(verify_api_key)])
def observe(request: ObserveRequest) -> ObserveResponse:
    return agent_service.observe(request)


@router.post("/decide", response_model=DecideResponse, dependencies=[Depends(verify_api_key)])
def decide(request: DecideRequest) -> DecideResponse:
    return agent_service.decide(request)
