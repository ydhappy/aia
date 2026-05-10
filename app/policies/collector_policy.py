from app.models.req import AgentState
from app.models.res import DecideResponse
from app.policies.base_policy import BaseRolePolicy


class CollectorPolicy(BaseRolePolicy):
    role_name = "collector"

    def decide(self, state: AgentState, profile: dict, recent_events: list[dict]) -> DecideResponse | None:
        has_loot_event = any(event.get("event_type") == "loot_detected" for event in recent_events)
        overweight = (state.weight_percent or 0) >= 85
        if has_loot_event and not overweight:
            return DecideResponse(
                action="PICKUP",
                action_args={"mode": "nearest_loot"},
                confidence=0.89,
                reason="collector_loot_priority",
                source="rule_engine",
            )

        if overweight and not state.safe_zone:
            return DecideResponse(
                action="RETREAT",
                action_args={"mode": "inventory_reset"},
                confidence=0.86,
                reason="collector_overweight_return",
                source="rule_engine",
            )

        patrol_points = profile.get("patrol_points", [])
        if patrol_points:
            return DecideResponse(
                action="MOVE",
                action_args={"mode": "patrol", "points": patrol_points[:3]},
                confidence=0.72,
                reason="collector_patrol_route",
                source="rule_engine",
            )

        return None


collector_policy = CollectorPolicy()
