from app.models.request_models import AgentState
from app.models.response_models import DecideResponse
from app.policies.base_policy import BaseRolePolicy


class SupportPolicy(BaseRolePolicy):
    role_name = "support"

    def decide(self, state: AgentState, profile: dict, recent_events: list[dict]) -> DecideResponse | None:
        banned_skills = set(profile.get("banned_skills", []))

        if state.nearby_allies > 0 and "buff" not in banned_skills and "buff" not in state.cooldowns:
            return DecideResponse(
                action="USE_SKILL",
                action_args={"skill": "buff", "target": "ally_group"},
                confidence=0.86,
                reason="support_group_buff",
                source="rule_engine",
            )

        if state.is_under_attack and state.target_distance is not None and state.target_distance > 1:
            return DecideResponse(
                action="MOVE",
                action_args={"mode": "reposition", "target_id": state.target_id},
                confidence=0.78,
                reason="support_reposition_under_threat",
                source="rule_engine",
            )

        return None


support_policy = SupportPolicy()
