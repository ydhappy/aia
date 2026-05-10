from app.models.req import AgentState
from app.models.res import DecideResponse
from app.policies.base_policy import BaseRolePolicy


class DealerPolicy(BaseRolePolicy):
    role_name = "dealer"

    def decide(self, state: AgentState, profile: dict, recent_events: list[dict]) -> DecideResponse | None:
        has_boss_event = any(event.get("event_type") == "boss_spawn" for event in recent_events)
        if has_boss_event and state.target_id:
            return DecideResponse(
                action="ATTACK",
                action_args={"target_id": state.target_id, "mode": "focus_fire"},
                confidence=0.93,
                reason="dealer_boss_focus",
                source="rule_engine",
            )

        if state.target_id and state.target_distance is not None and state.target_distance > 1:
            return DecideResponse(
                action="MOVE",
                action_args={"target_id": state.target_id, "mode": "approach"},
                confidence=0.84,
                reason="dealer_close_gap",
                source="rule_engine",
            )

        if state.target_id and state.target_distance is not None and state.target_distance <= 1:
            return DecideResponse(
                action="ATTACK",
                action_args={"target_id": state.target_id, "mode": "burst"},
                confidence=0.91,
                reason="dealer_burst_attack",
                source="rule_engine",
            )

        return None


dealer_policy = DealerPolicy()
