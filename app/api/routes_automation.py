from fastapi import APIRouter, Depends

from app.core.security import verify_api_key
from app.models.automation_models import (
    AutomationDecisionResponse,
    AutomationTaskListResponse,
    AutomationTaskRequest,
    AutomationTaskResponse,
)
from app.services.automation_service import automation_service
from app.services.store_factory import store


router = APIRouter(prefix="/automation", tags=["automation"], dependencies=[Depends(verify_api_key)])


@router.post("/task", response_model=AutomationTaskResponse)
def create_task(request: AutomationTaskRequest) -> AutomationTaskResponse:
    return automation_service.create_task(request)


@router.get("/{agent_id}/tasks", response_model=AutomationTaskListResponse)
def list_tasks(agent_id: str) -> AutomationTaskListResponse:
    return automation_service.list_tasks(agent_id)


@router.get("/{agent_id}/next-step", response_model=AutomationDecisionResponse)
def next_step(agent_id: str) -> AutomationDecisionResponse:
    state_wrapper = store.get_state(agent_id) or {}
    state = state_wrapper.get("state", {}) if isinstance(state_wrapper, dict) else {}
    return automation_service.decide_next_step(agent_id, state)
