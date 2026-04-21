from app.core.config import settings
from app.models.request_models import AgentState
from app.models.response_models import DecideResponse
from app.policies import ROLE_POLICIES
from app.services.adaptive_policy import adaptive_policy


class PolicyEngine:
    def decide(
        self,
        state: AgentState,
        profile: dict | None = None,
        recent_events: list[dict] | None = None,
        learning_state: dict | None = None,
        runtime_override: dict | None = None,
        growth_state: dict | None = None,
    ) -> DecideResponse:
        profile = profile or {}
        recent_events = recent_events or []
        learning_state = learning_state or {}
        runtime_override = runtime_override or {}
        growth_state = growth_state or {}

        override = runtime_override.get("override", {}) if isinstance(runtime_override, dict) else {}
        potion_count = state.inventory.get("potion", 0)
        role = override.get("role", profile.get("role", "custom"))
        style = override.get("style", profile.get("style", "balanced"))
        patrol_points = override.get("patrol_points", profile.get("patrol_points", []))
        retreat_hp_threshold = int(override.get("retreat_hp_threshold", settings.default_retreat_hp_threshold))
        forced_action = override.get("forced_action")
        forced_mode = override.get("forced_mode")
        growth_stage = growth_state.get("stage", "novice")

        if growth_stage == "novice":
            retreat_hp_threshold = max(retreat_hp_threshold, settings.default_retreat_hp_threshold + 5)
            if style == "balanced":
                style = "defensive"
        elif growth_stage in {"optimized", "expert"} and style == "balanced":
            style = "aggressive"

        has_danger_event = any(event.get("severity") == "high" for event in recent_events)
        is_overweight = state.weight_percent is not None and state.weight_percent >= 85

        if forced_action in {"MOVE", "ATTACK", "USE_SKILL", "RETREAT", "PICKUP", "IDLE"}:
            return adaptive_policy.adjust(DecideResponse(
                action=forced_action,
                action_args={"mode": forced_mode} if forced_mode else {},
                confidence=0.99,
                reason="runtime_override_forced_action",
                source="rule_engine",
            ), learning_state)

        if (state.hp <= retreat_hp_threshold or has_danger_event) and not state.safe_zone:
            mode = override.get("retreat_mode") or ("teleport" if state.can_teleport else "safe_zone")
            return adaptive_policy.adjust(DecideResponse(
                action="RETREAT",
                action_args={"mode": mode, "role": role, "growth_stage": growth_stage},
                confidence=0.99,
                reason="critical_hp_or_high_severity_event",
                source="rule_engine",
            ), learning_state)

        if is_overweight and not state.safe_zone:
            return adaptive_policy.adjust(DecideResponse(
                action="RETREAT",
                action_args={"mode": "inventory_reset", "growth_stage": growth_stage},
                confidence=0.87,
                reason="inventory_weight_high",
                source="rule_engine",
            ), learning_state)

        for policy in ROLE_POLICIES:
            if policy.applies(role):
                decision = policy.decide(state, profile, recent_events)
                if decision is not None:
                    decision.action_args = {**decision.action_args, "growth_stage": growth_stage}
                    return adaptive_policy.adjust(decision, learning_state)

        if state.hp <= settings.default_heal_hp_threshold and potion_count > 0:
            return adaptive_policy.adjust(DecideResponse(
                action="PICKUP",
                action_args={"item": "potion_buffer", "growth_stage": growth_stage},
                confidence=0.60,
                reason="low_hp_and_need_resources",
                source="rule_engine",
            ), learning_state)

        if style == "defensive" and state.is_under_attack and state.target_distance is not None and state.target_distance > 1 and not state.safe_zone:
            return adaptive_policy.adjust(DecideResponse(
                action="MOVE",
                action_args={"mode": override.get("move_mode", "kite"), "target_id": state.target_id, "growth_stage": growth_stage},
                confidence=0.84,
                reason="defensive_style_kiting",
                source="rule_engine",
            ), learning_state)

        if state.target_id and state.target_distance is not None and state.target_distance <= 1:
            return adaptive_policy.adjust(DecideResponse(
                action="ATTACK",
                action_args={"target_id": state.target_id, "style": style, "growth_stage": growth_stage},
                confidence=0.95 if growth_stage != "novice" else 0.88,
                reason="target_in_melee_range",
                source="rule_engine",
            ), learning_state)

        if state.target_id and state.target_distance is not None and state.target_distance > 1:
            return adaptive_policy.adjust(DecideResponse(
                action="MOVE",
                action_args={"target_id": state.target_id, "mode": override.get("move_mode", "approach"), "growth_stage": growth_stage},
                confidence=0.85,
                reason="target_visible_but_not_in_range",
                source="rule_engine",
            ), learning_state)

        if patrol_points:
            return adaptive_policy.adjust(DecideResponse(
                action="MOVE",
                action_args={"mode": override.get("move_mode", "patrol"), "points": patrol_points[:3], "growth_stage": growth_stage},
                confidence=0.70,
                reason="patrol_route_available",
                source="rule_engine",
            ), learning_state)

        return adaptive_policy.adjust(DecideResponse(
            action="IDLE",
            action_args={"role": role, "growth_stage": growth_stage},
            confidence=0.80,
            reason="no_target_and_no_urgent_state",
            source="rule_engine",
        ), learning_state)


policy_engine = PolicyEngine()
