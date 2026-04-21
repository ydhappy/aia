from app.services.goal_service import goal_service
from app.services.store_factory import store


class StateMachineService:
    def next_state(self, agent_id: str) -> dict:
        goal_state = goal_service.build_goal_state(agent_id)
        current = store.get_learning_state(f"fsm::{agent_id}") or {}
        current_phase = current.get("phase", "idle")
        next_phase = self._transition(current_phase, goal_state.next_phase)
        current["phase"] = next_phase
        current["goal"] = goal_state.primary_goal
        current["notes"] = goal_state.notes
        store.save_learning_state(f"fsm::{agent_id}", current)
        return current

    def _transition(self, current_phase: str, suggested_phase: str) -> str:
        if current_phase == suggested_phase:
            return current_phase
        return suggested_phase


state_machine_service = StateMachineService()
