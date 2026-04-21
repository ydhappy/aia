from app.core.config import settings
from app.models.response_models import DecideResponse


class AdaptivePolicy:
    def adjust(self, decision: DecideResponse, learning_state: dict | None = None) -> DecideResponse:
        learning_state = learning_state or {}
        preferred_action = learning_state.get("preferred_action")
        avoid_action = learning_state.get("avoid_action")

        if preferred_action and decision.action == preferred_action:
            decision.confidence = min(1.0, decision.confidence + settings.adaptive_preferred_bonus)
            decision.reason = f"{decision.reason}|preferred_action_bias"

        if avoid_action and decision.action == avoid_action:
            decision.confidence = max(0.05, decision.confidence - settings.adaptive_avoid_penalty)
            decision.reason = f"{decision.reason}|avoid_action_penalty"

        return decision


adaptive_policy = AdaptivePolicy()
