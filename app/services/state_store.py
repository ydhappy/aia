from collections import defaultdict
from typing import Any


class InMemoryStateStore:
    def __init__(self) -> None:
        self._states: dict[str, dict[str, Any]] = {}
        self._profiles: dict[str, dict[str, Any]] = {}
        self._events: dict[str, list[dict[str, Any]]] = {}
        self._traces: dict[str, dict[str, Any]] = {}
        self._learning: dict[str, dict[str, Any]] = {}
        self._metrics = defaultdict(int)

    def save_state(self, agent_id: str, tick: int, state: dict[str, Any]) -> None:
        self._states[agent_id] = {
            "tick": tick,
            "state": state,
        }
        self._metrics["total_observe_requests"] += 1

    def get_state(self, agent_id: str) -> dict[str, Any] | None:
        return self._states.get(agent_id)

    def save_profile(self, agent_id: str, profile: dict[str, Any]) -> None:
        self._profiles[agent_id] = profile
        self._metrics["total_profiles_saved"] += 1

    def get_profile(self, agent_id: str) -> dict[str, Any]:
        return self._profiles.get(agent_id, {})

    def save_event(self, agent_id: str, event: dict[str, Any]) -> None:
        events = self._events.setdefault(agent_id, [])
        events.append(event)
        self._events[agent_id] = events[-20:]
        self._metrics["total_events_saved"] += 1

    def get_recent_events(self, agent_id: str, limit: int = 10) -> list[dict[str, Any]]:
        return self._events.get(agent_id, [])[-limit:]

    def save_trace(self, agent_id: str, trace: dict[str, Any]) -> None:
        self._traces[agent_id] = trace

    def get_trace(self, agent_id: str) -> dict[str, Any]:
        return self._traces.get(agent_id, {})

    def save_learning_state(self, agent_id: str, learning_state: dict[str, Any]) -> None:
        self._learning[agent_id] = learning_state

    def get_learning_state(self, agent_id: str) -> dict[str, Any]:
        return self._learning.get(agent_id, {})

    def increment_decide(self) -> None:
        self._metrics["total_decide_requests"] += 1

    def increment_fallback(self) -> None:
        self._metrics["total_fallbacks"] += 1

    def metrics(self) -> dict[str, int]:
        return {
            "total_observe_requests": self._metrics["total_observe_requests"],
            "total_decide_requests": self._metrics["total_decide_requests"],
            "total_fallbacks": self._metrics["total_fallbacks"],
            "total_profiles_saved": self._metrics["total_profiles_saved"],
            "total_events_saved": self._metrics["total_events_saved"],
        }


state_store = InMemoryStateStore()
