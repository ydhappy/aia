from fastapi import APIRouter, Depends

from app.core.security import verify_api_key
from app.models.response_models import RobotEventResponse, RobotProfileResponse
from app.models.unified_api_models import (
    AiaRobotOpsTickRequest,
    AiaRobotOpsTickResponse,
    UnifiedRobotSyncRequest,
    UnifiedRobotSyncResponse,
)
from app.services.agent_service import agent_service
from app.services.automation_service import automation_service
from app.services.robot_autonomy_baseline_service import robot_autonomy_baseline_service
from app.services.learning_service import learning_service
from app.services.robot_ai_ops_service import robot_ai_ops_service
from app.services.store_factory import store


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


@router.post("/robot/ops-tick", response_model=AiaRobotOpsTickResponse)
def robot_ops_tick(request: AiaRobotOpsTickRequest) -> AiaRobotOpsTickResponse:
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

    agent_id = _resolve_agent_id(request)
    state = _resolve_state_payload(request)
    agent_state = _resolve_agent_state(request)
    automation_next_step = automation_service.decide_next_step(agent_id, state).next_step if agent_id else {}
    learning_state = store.get_learning_state(agent_id) if agent_id else {}
    base_profile = store.get_profile(agent_id) if agent_id else {}
    autonomy_profile = (
        robot_autonomy_baseline_service.resolve_profile(agent_id, agent_state, base_profile, learning_state)
        if agent_id and agent_state is not None
        else base_profile
    )
    assessment = robot_ai_ops_service.assess_state(agent_state) if agent_state is not None else {}
    talk_suggestion = (
        robot_autonomy_baseline_service.build_talk_suggestion(agent_id, agent_state, autonomy_profile, learning_state, assessment)
        if agent_id and agent_state is not None
        else {}
    )
    agent_ids = [agent_id] if agent_id else []
    dashboard = robot_ai_ops_service.dashboard_snapshot(agent_ids) if request.include_dashboard else None
    checklist_status = _checklist_status(dashboard)
    server_contract = (
        dashboard.server_minimal_contract
        if dashboard is not None
        else robot_ai_ops_service.server_minimal_contract()
    )

    return AiaRobotOpsTickResponse(
        agent_id=agent_id,
        profile_result=profile_result,
        event_results=event_results,
        observe_result=observe_result,
        decide_result=decide_result,
        feedback_result=feedback_result,
        automation_result=automation_result,
        automation_next_step=automation_next_step,
        dashboard=dashboard,
        checklist_status=checklist_status,
        server_minimal_contract=server_contract,
        autonomy_profile=autonomy_profile,
        talk_suggestion=talk_suggestion,
        cleanup_policy=robot_autonomy_baseline_service.cleanup_policy(),
    )


def _resolve_agent_id(request: AiaRobotOpsTickRequest) -> str:
    if request.decide is not None:
        return request.decide.agent_id
    if request.observe is not None:
        return request.observe.agent_id
    if request.profile is not None:
        return request.profile.agent_id
    if request.feedback is not None:
        return request.feedback.agent_id
    if request.events:
        return request.events[0].agent_id
    if request.automation_task is not None:
        return request.automation_task.agent_id
    return ""


def _resolve_state_payload(request: AiaRobotOpsTickRequest) -> dict:
    if request.decide is not None:
        return request.decide.state.model_dump()
    if request.observe is not None:
        return request.observe.state.model_dump()
    return {}


def _resolve_agent_state(request: AiaRobotOpsTickRequest):
    if request.decide is not None:
        return request.decide.state
    if request.observe is not None:
        return request.observe.state
    return None


def _checklist_status(dashboard) -> str:
    if dashboard is None:
        return "not_requested"
    if any(item.status == "warn" for item in dashboard.checklist):
        return "warn"
    return "pass"
