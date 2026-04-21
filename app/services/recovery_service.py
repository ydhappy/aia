from app.models.admin_models import RecoveryActionResponse
from app.services.automation_service import automation_service
from app.services.store_factory import store


class RecoveryService:
    def recover_agent(self, agent_id: str) -> RecoveryActionResponse:
        state_wrapper = store.get_state(agent_id) or {}
        state = state_wrapper.get("state", {}) if isinstance(state_wrapper, dict) else {}
        trace = store.get_trace(agent_id) or {}

        if not state:
            return RecoveryActionResponse(
                agent_id=agent_id,
                action="noop",
                message="no_state_available_for_recovery",
            )

        if state.get("hp", 100) <= 20:
            return RecoveryActionResponse(
                agent_id=agent_id,
                action="force_retreat",
                message="low_hp_detected_force_retreat",
            )

        final_reason = str(trace.get("final_reason", ""))
        if "invalid_decision" in final_reason:
            tasks = automation_service.list_tasks(agent_id).tasks
            if tasks:
                task_id = tasks[0].task_id
                automation_service.update_task_status(agent_id, task_id, "paused")
                return RecoveryActionResponse(
                    agent_id=agent_id,
                    action="pause_task",
                    message="invalid_decision_detected_task_paused",
                )
            return RecoveryActionResponse(
                agent_id=agent_id,
                action="idle_fallback",
                message="invalid_decision_without_task_idle_fallback",
            )

        if trace.get("llm_validation_error"):
            return RecoveryActionResponse(
                agent_id=agent_id,
                action="rule_only_mode",
                message="llm_validation_error_detected_switch_to_rule_fallback",
            )

        return RecoveryActionResponse(
            agent_id=agent_id,
            action="stable",
            message="no_recovery_action_needed",
        )


recovery_service = RecoveryService()
