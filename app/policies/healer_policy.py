from app.models.req import AgentState
from app.models.res import DecideResponse
from app.policies.base_policy import BaseRolePolicy


class HealerPolicy(BaseRolePolicy):
    role_name = "healer"

    def decide(self, state: AgentState, profile: dict, recent_events: list[dict]) -> DecideResponse | None:
        preferred_skills = set(profile.get("preferred_skills", []))
        banned_skills = set(profile.get("banned_skills", []))

        if state.hp <= 50 and state.cooldowns.get("heal", 999) == 0 and "heal" not in banned_skills:
            return DecideResponse(
                action="USE_SKILL",
                action_args={"skill": "heal", "target": "self"},
                confidence=0.97,
                reason="healer_low_hp_self_heal",
                source="rule_engine",
            )

        if state.nearby_allies > 0 and "support_heal" in preferred_skills and "support_heal" not in banned_skills:
            return DecideResponse(
                action="USE_SKILL",
                action_args={"skill": "support_heal", "target": "ally_or_self"},
                confidence=0.90,
                reason="healer_group_support",
                source="rule_engine",
            )

        return None


healer_policy = HealerPolicy()
