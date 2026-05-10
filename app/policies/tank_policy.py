from app.models.req import AgentState
from app.models.res import DecideResponse
from app.policies.base_policy import BaseRolePolicy


class TankPolicy(BaseRolePolicy):
    role_name = "tank"

    def decide(self, state: AgentState, profile: dict, recent_events: list[dict]) -> DecideResponse | None:
        banned_skills = set(profile.get("banned_skills", []))
        if state.target_id and state.nearby_enemies >= 2:
            skill_name = "taunt" if "taunt" not in banned_skills else "shield"
            return DecideResponse(
                action="USE_SKILL",
                action_args={"skill": skill_name, "target": state.target_id},
                confidence=0.88,
                reason="tank_multi_target_control",
                source="rule_engine",
            )

        if state.target_id and state.target_distance is not None and state.target_distance <= 1:
            return DecideResponse(
                action="ATTACK",
                action_args={"target_id": state.target_id, "mode": "frontline"},
                confidence=0.90,
                reason="tank_frontline_attack",
                source="rule_engine",
            )

        return None


tank_policy = TankPolicy()
