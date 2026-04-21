from typing import Any

from app.models.request_models import AgentState


class AgentGraph:
    def run(
        self,
        agent_id: str,
        state: AgentState,
        profile: dict[str, Any] | None = None,
        recent_events: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        profile = profile or {}
        recent_events = recent_events or []

        risk_score = self._evaluate_risk(state, recent_events)
        strategy = self._choose_strategy(state, profile, risk_score)
        llm_hint = self._should_request_llm_hint(state, profile, recent_events, risk_score)

        return {
            "agent_id": agent_id,
            "risk_score": risk_score,
            "strategy": strategy,
            "llm_hint": llm_hint,
            "profile": profile,
            "recent_events": recent_events,
            "state": state.model_dump(),
        }

    def _evaluate_risk(self, state: AgentState, recent_events: list[dict[str, Any]]) -> int:
        score = 0
        if state.hp <= 30:
            score += 4
        elif state.hp <= 50:
            score += 2

        score += min(state.nearby_enemies, 3)
        score += 1 if state.is_under_attack else 0
        score += 2 if any(event.get("severity") == "high" for event in recent_events) else 0
        score += 1 if "stun" in state.debuffs else 0
        return score

    def _choose_strategy(self, state: AgentState, profile: dict[str, Any], risk_score: int) -> str:
        role = profile.get("role", "custom")
        style = profile.get("style", "balanced")

        if risk_score >= 5:
            return "survival"
        if role == "collector":
            return "loot"
        if role == "healer":
            return "support"
        if role == "tank":
            return "control"
        if style == "aggressive":
            return "pressure"
        if state.target_id:
            return "engage"
        return "patrol"

    def _should_request_llm_hint(
        self,
        state: AgentState,
        profile: dict[str, Any],
        recent_events: list[dict[str, Any]],
        risk_score: int,
    ) -> bool:
        extras = state.extras or {}
        if extras.get("require_llm", False):
            return True
        if risk_score >= 5 and len(recent_events) >= 2:
            return True
        if profile.get("notes"):
            return True
        return False


agent_graph = AgentGraph()
