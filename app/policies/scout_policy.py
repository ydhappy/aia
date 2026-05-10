from app.models.req import AgentState
from app.models.res import DecideResponse
from app.policies.base_policy import BaseRolePolicy


class ScoutPolicy(BaseRolePolicy):
    role_name = "scout"

    def decide(self, state: AgentState, profile: dict, recent_events: list[dict]) -> DecideResponse | None:
        patrol_points = profile.get("patrol_points", [])
        has_danger_event = any(event.get("severity") == "high" for event in recent_events)

        if has_danger_event and not state.safe_zone:
            return DecideResponse(
                action="RETREAT",
                action_args={"mode": "report_and_fall_back"},
                confidence=0.88,
                reason="scout_high_risk_retreat",
                source="rule_engine",
            )

        if patrol_points:
            return DecideResponse(
                action="MOVE",
                action_args={"mode": "scout_patrol", "points": patrol_points[:4]},
                confidence=0.82,
                reason="scout_patrol_cycle",
                source="rule_engine",
            )

        if state.target_id and state.target_distance is not None and state.target_distance > 1:
            return DecideResponse(
                action="MOVE",
                action_args={"mode": "observe_target", "target_id": state.target_id},
                confidence=0.76,
                reason="scout_observe_target",
                source="rule_engine",
            )

        return None


scout_policy = ScoutPolicy()
