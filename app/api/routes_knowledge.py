from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import verify_api_key
from app.models.req import (
    RobotEventRequest,
    RobotFeedbackRequest,
    RobotLearningDigestRequest,
    RobotProfilePatchRequest,
    RobotProfileRequest,
    RobotSpawnRequestCreateRequest,
)
from app.models.res import (
    AgentTraceResponse,
    RobotDeleteResponse,
    RobotEventResponse,
    RobotFeedbackResponse,
    RobotKnowledgeResponse,
    RobotLearningDigestResponse,
    RobotLearningStateResponse,
    RobotListResponse,
    RobotProfileResponse,
)
from app.services.agent_service import agent_service
from app.services.learning_service import learning_service
from app.services.robot_learning_digest_service import robot_learning_digest_service
from app.services.spawn import robot_spawn_request_service
from app.services.store_factory import store


router = APIRouter(prefix="/robot", tags=["robot"], dependencies=[Depends(verify_api_key)])


def _raise_not_found(agent_id: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "robot_not_found", "agent_id": agent_id},
    )


@router.get("", response_model=RobotListResponse)
def list_robots() -> RobotListResponse:
    agent_ids = store.list_agent_ids()
    return RobotListResponse(count=len(agent_ids), agent_ids=agent_ids)


@router.post("/spawn-requests")
def create_spawn_requests(request: RobotSpawnRequestCreateRequest) -> dict:
    return robot_spawn_request_service.create_requests(request)


@router.post("/profile", response_model=RobotProfileResponse)
def save_profile(request: RobotProfileRequest) -> RobotProfileResponse:
    store.save_profile(request.agent_id, request.model_dump())
    return RobotProfileResponse(agent_id=request.agent_id)


@router.put("/{agent_id}/profile", response_model=RobotProfileResponse)
def replace_profile(agent_id: str, request: RobotProfileRequest) -> RobotProfileResponse:
    profile = request.model_dump()
    profile["agent_id"] = agent_id
    store.save_profile(agent_id, profile)
    return RobotProfileResponse(agent_id=agent_id, message="robot profile replaced")


@router.patch("/{agent_id}/profile", response_model=RobotProfileResponse)
def patch_profile(agent_id: str, request: RobotProfilePatchRequest) -> RobotProfileResponse:
    if not store.has_agent(agent_id):
        _raise_not_found(agent_id)
    patch = request.model_dump(exclude_unset=True)
    store.update_profile(agent_id, patch)
    return RobotProfileResponse(agent_id=agent_id, message="robot profile updated")


@router.delete("/{agent_id}", response_model=RobotDeleteResponse)
def delete_robot(agent_id: str) -> RobotDeleteResponse:
    deleted = store.delete_agent(agent_id)
    if not deleted:
        _raise_not_found(agent_id)
    return RobotDeleteResponse(agent_id=agent_id, deleted=True)


@router.post("/event", response_model=RobotEventResponse)
def save_event(request: RobotEventRequest) -> RobotEventResponse:
    store.save_event(request.agent_id, request.model_dump())
    return RobotEventResponse(agent_id=request.agent_id)


@router.post("/feedback", response_model=RobotFeedbackResponse)
def submit_feedback(request: RobotFeedbackRequest) -> RobotFeedbackResponse:
    return learning_service.submit_feedback(request)


@router.post("/learning/digest", response_model=RobotLearningDigestResponse)
def apply_learning_digest(request: RobotLearningDigestRequest) -> RobotLearningDigestResponse:
    return robot_learning_digest_service.apply_digest(request)


@router.get("/learning/summary")
def learning_summary() -> dict:
    return robot_learning_digest_service.summary()


@router.get("/{agent_id}", response_model=RobotKnowledgeResponse)
def get_robot_knowledge(agent_id: str) -> RobotKnowledgeResponse:
    if not store.has_agent(agent_id):
        _raise_not_found(agent_id)
    return RobotKnowledgeResponse(
        agent_id=agent_id,
        profile=store.get_profile(agent_id),
        recent_events=store.get_recent_events(agent_id),
        last_state=store.get_state(agent_id),
    )


@router.get("/{agent_id}/trace", response_model=AgentTraceResponse)
def get_agent_trace(agent_id: str) -> AgentTraceResponse:
    if not store.has_agent(agent_id):
        _raise_not_found(agent_id)
    return agent_service.get_trace(agent_id)


@router.get("/{agent_id}/learning", response_model=RobotLearningStateResponse)
def get_learning_state(agent_id: str) -> RobotLearningStateResponse:
    if not store.has_agent(agent_id):
        _raise_not_found(agent_id)
    return learning_service.get_learning_state(agent_id)
