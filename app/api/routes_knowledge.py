from fastapi import APIRouter

from app.models.request_models import RobotEventRequest, RobotProfileRequest
from app.models.response_models import AgentTraceResponse, RobotEventResponse, RobotKnowledgeResponse, RobotProfileResponse
from app.services.agent_service import agent_service
from app.services.state_store import state_store


router = APIRouter(prefix="/robot", tags=["robot"])


@router.post("/profile", response_model=RobotProfileResponse)
def save_profile(request: RobotProfileRequest) -> RobotProfileResponse:
    state_store.save_profile(request.agent_id, request.model_dump())
    return RobotProfileResponse(agent_id=request.agent_id)


@router.post("/event", response_model=RobotEventResponse)
def save_event(request: RobotEventRequest) -> RobotEventResponse:
    state_store.save_event(request.agent_id, request.model_dump())
    return RobotEventResponse(agent_id=request.agent_id)


@router.get("/{agent_id}", response_model=RobotKnowledgeResponse)
def get_robot_knowledge(agent_id: str) -> RobotKnowledgeResponse:
    return RobotKnowledgeResponse(
        agent_id=agent_id,
        profile=state_store.get_profile(agent_id),
        recent_events=state_store.get_recent_events(agent_id),
        last_state=state_store.get_state(agent_id),
    )


@router.get("/{agent_id}/trace", response_model=AgentTraceResponse)
def get_agent_trace(agent_id: str) -> AgentTraceResponse:
    return agent_service.get_trace(agent_id)
