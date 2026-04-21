from fastapi import APIRouter

from app.models.request_models import DecideRequest, ObserveRequest
from app.models.response_models import DecideResponse, ObserveResponse
from app.services.agent_service import agent_service


router = APIRouter(tags=["agent"])


@router.post("/observe", response_model=ObserveResponse)
def observe(request: ObserveRequest) -> ObserveResponse:
    return agent_service.observe(request)


@router.post("/decide", response_model=DecideResponse)
def decide(request: DecideRequest) -> DecideResponse:
    return agent_service.decide(request)
