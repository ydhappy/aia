from app.models.goal_models import GoalStateResponse
from app.services.store_factory import store


class GoalService:
    def build_goal_state(self, agent_id: str) -> GoalStateResponse:
        state_wrapper = store.get_state(agent_id) or {}
        state = state_wrapper.get("state", {}) if isinstance(state_wrapper, dict) else {}
        profile = store.get_profile(agent_id) or {}
        learning = store.get_learning_state(agent_id) or {}

        hp = int(state.get("hp", 100) or 100)
        safe_zone = bool(state.get("safe_zone", False))
        weight_percent = int(state.get("weight_percent", 0) or 0)
        role = profile.get("role", "custom")
        preferred_action = learning.get("preferred_action")

        if hp <= 30:
            return GoalStateResponse(
                agent_id=agent_id,
                primary_goal="survive",
                secondary_goals=["retreat", "recover"],
                next_phase="return_to_safe_zone",
                notes=["low_hp_priority"],
            )

        if weight_percent >= 85:
            return GoalStateResponse(
                agent_id=agent_id,
                primary_goal="logistics",
                secondary_goals=["return_base", "inventory_reset"],
                next_phase="return_and_resume",
                notes=["overweight_detected"],
            )

        if safe_zone:
            return GoalStateResponse(
                agent_id=agent_id,
                primary_goal="resume_field_operation",
                secondary_goals=[role, preferred_action or "engage"],
                next_phase="leave_safe_zone",
                notes=["safe_zone_ready"],
            )

        if role == "collector":
            return GoalStateResponse(
                agent_id=agent_id,
                primary_goal="loot_and_farm",
                secondary_goals=["loot_cycle", "resource_efficiency"],
                next_phase="field_collection",
                notes=[preferred_action or "pickup_focus"],
            )

        if role in {"healer", "support"}:
            return GoalStateResponse(
                agent_id=agent_id,
                primary_goal="party_support",
                secondary_goals=["follow_party", "maintain_group"],
                next_phase="support_loop",
                notes=[preferred_action or "support_focus"],
            )

        return GoalStateResponse(
            agent_id=agent_id,
            primary_goal="combat_progression",
            secondary_goals=[role, preferred_action or "attack_focus"],
            next_phase="combat_loop",
            notes=["normal_operation"],
        )


goal_service = GoalService()
