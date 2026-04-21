from app.core.config import settings
from app.models.request_models import AgentState
from app.models.response_models import DecideResponse


class PolicyEngine:
    def decide(
        self,
        state: AgentState,
        profile: dict | None = None,
        recent_events: list[dict] | None = None,
    ) -> DecideResponse:
        profile = profile or {}
        recent_events = recent_events or []

        heal_cd = state.cooldowns.get("heal", 999)
        potion_count = state.inventory.get("potion", 0)
        role = profile.get("role", "custom")
        style = profile.get("style", "balanced")
        preferred_skills = set(profile.get("preferred_skills", []))
        banned_skills = set(profile.get("banned_skills", []))

        has_danger_event = any(event.get("severity") == "high" for event in recent_events)
        has_loot_event = any(event.get("event_type") == "loot_detected" for event in recent_events)

        if state.hp <= settings.default_retreat_hp_threshold or has_danger_event:
            return DecideResponse(
                action="RETREAT",
                action_args={"mode": "safe_zone", "role": role},
                confidence=0.99,
                reason="critical_hp_or_high_severity_event",
                source="rule_engine",
            )

        if (
            state.hp <= settings.default_heal_hp_threshold
            and heal_cd == 0
            and "heal" not in banned_skills
        ):
            return DecideResponse(
                action="USE_SKILL",
                action_args={"skill": "heal", "target": "self"},
                confidence=0.98,
                reason="low_hp_and_heal_ready",
                source="rule_engine",
            )

        if role == "healer" and state.target_id and state.target_distance is not None and state.target_distance <= 3:
            skill_name = "support_heal" if "support_heal" in preferred_skills else "heal"
            if skill_name not in banned_skills:
                return DecideResponse(
                    action="USE_SKILL",
                    action_args={"skill": skill_name, "target": "ally_or_self"},
                    confidence=0.88,
                    reason="healer_role_support_action",
                    source="rule_engine",
                )

        if style == "defensive" and state.is_under_attack and state.target_distance is not None and state.target_distance > 1:
            return DecideResponse(
                action="MOVE",
                action_args={"mode": "kite", "target_id": state.target_id},
                confidence=0.84,
                reason="defensive_style_kiting",
                source="rule_engine",
            )

        if role == "collector" and has_loot_event:
            return DecideResponse(
                action="PICKUP",
                action_args={"mode": "nearest_loot"},
                confidence=0.86,
                reason="collector_role_loot_detected",
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
                action_args={"target_id": state.target_id, "style": style},
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
            action_args={"role": role},
            confidence=0.80,
            reason="no_target_and_no_urgent_state",
            source="rule_engine",
        )


policy_engine = PolicyEngine()
