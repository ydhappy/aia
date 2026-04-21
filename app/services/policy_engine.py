from app.core.config import settings
from app.models.request_models import AgentState
from app.models.response_models import DecideResponse


class PolicyEngine:
    def decide(self, state: AgentState) -> DecideResponse:
        heal_cd = state.cooldowns.get("heal", 999)
        potion_count = state.inventory.get("potion", 0)

        if state.hp <= settings.default_retreat_hp_threshold:
            return DecideResponse(
                action="RETREAT",
                action_args={"mode": "safe_zone"},
                confidence=0.99,
                reason="critical_hp",
                source="rule_engine",
            )

        if state.hp <= settings.default_heal_hp_threshold and heal_cd == 0:
            return DecideResponse(
                action="USE_SKILL",
                action_args={"skill": "heal", "target": "self"},
                confidence=0.98,
                reason="low_hp_and_heal_ready",
                source="rule_engine",
            )

        if state.hp <= settings.default_heal_hp_threshold and potion_count > 0:
            return DecideResponse(
                action="PICKUP",
                action_args={"item": "potion_buffer"},
                confidence=0.60,
                reason="low_hp_and_need_resources",
                source="rule_engine",
            )

        if state.target_id and state.target_distance is not None and state.target_distance <= 1:
            return DecideResponse(
                action="ATTACK",
                action_args={"target_id": state.target_id},
                confidence=0.95,
                reason="target_in_melee_range",
                source="rule_engine",
            )

        if state.target_id and state.target_distance is not None and state.target_distance > 1:
            return DecideResponse(
                action="MOVE",
                action_args={"target_id": state.target_id, "mode": "approach"},
                confidence=0.85,
                reason="target_visible_but_not_in_range",
                source="rule_engine",
            )

        return DecideResponse(
            action="IDLE",
            action_args={},
            confidence=0.80,
            reason="no_target_and_no_urgent_state",
            source="rule_engine",
        )


policy_engine = PolicyEngine()
