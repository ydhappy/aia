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


@router.post("/{agent_id}/tasks/{task_id}/pause", response_model=AutomationTaskResponse)
def pause_task(agent_id: str, task_id: str) -> AutomationTaskResponse:
    return automation_service.update_task_status(agent_id, task_id, "paused")


@router.post("/{agent_id}/tasks/{task_id}/resume", response_model=AutomationTaskResponse)
def resume_task(agent_id: str, task_id: str) -> AutomationTaskResponse:
    return automation_service.update_task_status(agent_id, task_id, "running")


@router.delete("/{agent_id}/tasks/{task_id}", response_model=AutomationTaskResponse)
def delete_task(agent_id: str, task_id: str) -> AutomationTaskResponse:
    return automation_service.delete_task(agent_id, task_id)


@router.get("/{agent_id}/next-step", response_model=AutomationDecisionResponse)
def next_step(agent_id: str) -> AutomationDecisionResponse:
    state_wrapper = store.get_state(agent_id) or {}
    state = state_wrapper.get("state", {}) if isinstance(state_wrapper, dict) else {}
    return automation_service.decide_next_step(agent_id, state)
