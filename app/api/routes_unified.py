from fastapi import APIRouter, Depends

from app.core.security import verify_api_key
from app.models.unified_api_models import UnifiedRobotSyncRequest, UnifiedRobotSyncResponse
from app.services.agent_service import agent_service
from app.services.automation_service import automation_service
from app.services.learning_service import learning_service
from app.services.store_factory import store
from app.models.response_models import RobotEventResponse, RobotProfileResponse


router = APIRouter(prefix="/api/v1", tags=["unified"], dependencies=[Depends(verify_api_key)])


@router.post("/robot/sync", response_model=UnifiedRobotSyncResponse)
def robot_sync(request: UnifiedRobotSyncRequest) -> UnifiedRobotSyncResponse:
    profile_result = None
    event_results = []
    observe_result = None
    decide_result = None
    feedback_result = None
    automation_result = {}

    if request.profile is not None:
        store.save_profile(request.profile.agent_id, request.profile.model_dump())
        profile_result = RobotProfileResponse(agent_id=request.profile.agent_id)

    for event in request.events:
        store.save_event(event.agent_id, event.model_dump())
        event_results.append(RobotEventResponse(agent_id=event.agent_id))

    if request.observe is not None:
        observe_result = agent_service.observe(request.observe)

    if request.decide is not None:
        decide_result = agent_service.decide(request.decide)

    if request.feedback is not None:
        feedback_result = learning_service.submit_feedback(request.feedback)

    if request.automation_task is not None:
        automation_task_res = automation_service.create_task(request.automation_task)
        automation_result = automation_task_res.model_dump()

    return UnifiedRobotSyncResponse(
        profile_result=profile_result,
        event_results=event_results,
        observe_result=observe_result,
        decide_result=decide_result,
        feedback_result=feedback_result,
        automation_result=automation_result,
    )
