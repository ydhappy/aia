import uuid

from app.models.auto import (
    AutomationDecisionResponse,
    AutomationTaskListResponse,
    AutomationTaskRequest,
    AutomationTaskResponse,
    RobotAutomationTask,
)
from app.services.economy_service import economy_service
from app.services.goal_service import goal_service
from app.services.npc_service import npc_service
from app.services.state_machine_service import state_machine_service
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

    def update_task_status(self, agent_id: str, task_id: str, status: str) -> AutomationTaskResponse:
        current = store.get_learning_state(f"automation::{agent_id}") or {}
        tasks = current.get("tasks", [])
        for task in tasks:
            if task.get("task_id") == task_id:
                task["status"] = status
                break
        current["tasks"] = tasks
        store.save_learning_state(f"automation::{agent_id}", current)
        return AutomationTaskResponse(agent_id=agent_id, task_id=task_id, message=f"automation task {status}")

    def delete_task(self, agent_id: str, task_id: str) -> AutomationTaskResponse:
        current = store.get_learning_state(f"automation::{agent_id}") or {}
        tasks = current.get("tasks", [])
        tasks = [task for task in tasks if task.get("task_id") != task_id]
        current["tasks"] = tasks
        store.save_learning_state(f"automation::{agent_id}", current)
        return AutomationTaskResponse(agent_id=agent_id, task_id=task_id, message="automation task deleted")

    def decide_next_step(self, agent_id: str, state: dict) -> AutomationDecisionResponse:
        current = store.get_learning_state(f"automation::{agent_id}") or {}
        tasks = current.get("tasks", [])
        active_task = next((task for task in tasks if task.get("status") in {"pending", "running"}), {})
        goal_state = goal_service.build_goal_state(agent_id).model_dump()
        fsm_state = state_machine_service.next_state(agent_id)
        economy_state = economy_service.next_economy_step(agent_id)
        npc_state = npc_service.next_npc_step(agent_id)
        next_step = self._build_next_step(active_task, state, goal_state, fsm_state, economy_state, npc_state)
        return AutomationDecisionResponse(
            agent_id=agent_id,
            active_task=active_task,
            next_step=next_step,
        )

    def _build_next_step(
        self,
        active_task: dict,
        state: dict,
        goal_state: dict,
        fsm_state: dict,
        economy_state: dict,
        npc_state: dict,
    ) -> dict:
        phase = fsm_state.get("phase", "idle")
        goal = goal_state.get("primary_goal")

        if npc_state.get("phase") == "npc_interaction":
            return {
                "mode": "npc_interaction",
                "objective": npc_state.get("objective"),
                "npc_type": npc_state.get("npc_type"),
                "home_x": npc_state.get("home_x"),
                "home_y": npc_state.get("home_y"),
                "goal": goal,
                "phase": phase,
            }

        if economy_state.get("phase") in {"return_base", "inventory_reset", "resupply", "redeploy"}:
            return {
                "mode": economy_state.get("phase"),
                "objective": economy_state.get("objective"),
                "goal": goal,
                "phase": phase,
            }

        if phase == "return_to_safe_zone":
            return {
                "mode": "return_and_resume",
                "objective": "return_safe_zone_immediately",
                "goal": goal,
                "phase": phase,
            }
        if phase == "leave_safe_zone":
            return {
                "mode": "resume_field_operation",
                "objective": "leave_safe_zone_and_resume",
                "goal": goal,
                "phase": phase,
            }
        if not active_task:
            if phase == "field_collection":
                return {
                    "mode": "loot_loop",
                    "objective": "collect_resources",
                    "goal": goal,
                    "phase": phase,
                }
            if phase == "support_loop":
                return {
                    "mode": "support_loop",
                    "objective": "follow_and_support_party",
                    "goal": goal,
                    "phase": phase,
                }
            if phase == "combat_loop":
                return {
                    "mode": "farm",
                    "objective": "combat_and_progress",
                    "goal": goal,
                    "phase": phase,
                }
            return {
                "mode": "idle",
                "reason": "no_active_automation_task",
                "goal": goal,
                "phase": phase,
            }

        mode = active_task.get("mode")
        params = active_task.get("parameters", {})
        conditions = active_task.get("conditions", {})

        if mode == "farm":
            return {
                "mode": mode,
                "objective": "hunt_and_loot",
                "area": params.get("area"),
                "stop_when_hp_below": conditions.get("hp_below", 35),
                "goal": goal,
                "phase": phase,
            }
        if mode == "patrol":
            return {
                "mode": mode,
                "objective": "follow_patrol_points",
                "points": params.get("points", []),
                "goal": goal,
                "phase": phase,
            }
        if mode == "return_and_resume":
            return {
                "mode": mode,
                "objective": "return_base_then_resume",
                "resume_mode": params.get("resume_mode", "farm"),
                "goal": goal,
                "phase": phase,
            }
        if mode == "support_loop":
            return {
                "mode": mode,
                "objective": "follow_party_and_support",
                "party_id": params.get("party_id"),
                "goal": goal,
                "phase": phase,
            }
        if mode == "loot_loop":
            return {
                "mode": mode,
                "objective": "scan_and_pickup_loot",
                "area": params.get("area"),
                "goal": goal,
                "phase": phase,
            }
        if mode == "boss_watch":
            return {
                "mode": mode,
                "objective": "watch_spawn_and_engage_or_report",
                "boss_id": params.get("boss_id"),
                "goal": goal,
                "phase": phase,
            }
        return {
            "mode": mode,
            "objective": "custom_automation_step",
            "parameters": params,
            "goal": goal,
            "phase": phase,
        }


automation_service = AutomationService()
