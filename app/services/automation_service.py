import uuid

from app.models.automation_models import (
    AutomationDecisionResponse,
    AutomationTaskListResponse,
    AutomationTaskRequest,
    AutomationTaskResponse,
    RobotAutomationTask,
)
from app.services.store_factory import store


class AutomationService:
    def create_task(self, request: AutomationTaskRequest) -> AutomationTaskResponse:
        task = RobotAutomationTask(
            task_id=str(uuid.uuid4()),
            agent_id=request.agent_id,
            mode=request.mode,
            priority=request.priority,
            conditions=request.conditions,
            parameters=request.parameters,
        )
        current = store.get_learning_state(f"automation::{request.agent_id}") or {}
        tasks = current.get("tasks", [])
        tasks.append(task.model_dump())
        tasks.sort(key=lambda item: item.get("priority", 50), reverse=True)
        current["tasks"] = tasks
        store.save_learning_state(f"automation::{request.agent_id}", current)
        return AutomationTaskResponse(agent_id=request.agent_id, task_id=task.task_id)

    def list_tasks(self, agent_id: str) -> AutomationTaskListResponse:
        current = store.get_learning_state(f"automation::{agent_id}") or {}
        tasks = [RobotAutomationTask(**item) for item in current.get("tasks", [])]
        return AutomationTaskListResponse(agent_id=agent_id, tasks=tasks)

    def decide_next_step(self, agent_id: str, state: dict) -> AutomationDecisionResponse:
        current = store.get_learning_state(f"automation::{agent_id}") or {}
        tasks = current.get("tasks", [])
        active_task = tasks[0] if tasks else {}
        next_step = self._build_next_step(active_task, state)
        return AutomationDecisionResponse(
            agent_id=agent_id,
            active_task=active_task,
            next_step=next_step,
        )

    def _build_next_step(self, active_task: dict, state: dict) -> dict:
        if not active_task:
            return {"mode": "idle", "reason": "no_active_automation_task"}

        mode = active_task.get("mode")
        params = active_task.get("parameters", {})
        conditions = active_task.get("conditions", {})

        if mode == "farm":
            return {
                "mode": mode,
                "objective": "hunt_and_loot",
                "area": params.get("area"),
                "stop_when_hp_below": conditions.get("hp_below", 35),
            }
        if mode == "patrol":
            return {
                "mode": mode,
                "objective": "follow_patrol_points",
                "points": params.get("points", []),
            }
        if mode == "return_and_resume":
            return {
                "mode": mode,
                "objective": "return_base_then_resume",
                "resume_mode": params.get("resume_mode", "farm"),
            }
        if mode == "support_loop":
            return {
                "mode": mode,
                "objective": "follow_party_and_support",
                "party_id": params.get("party_id"),
            }
        return {
            "mode": mode,
            "objective": "custom_automation_step",
            "parameters": params,
        }


automation_service = AutomationService()
