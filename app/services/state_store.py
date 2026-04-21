from collections import defaultdict
from typing import Any


class InMemoryStateStore:
    def __init__(self) -> None:
        self._states: dict[str, dict[str, Any]] = {}
        self._metrics = defaultdict(int)

    def save_state(self, agent_id: str, tick: int, state: dict[str, Any]) -> None:
        self._states[agent_id] = {
            "tick": tick,
            "state": state,
        }
        self._metrics["total_observe_requests"] += 1

    def get_state(self, agent_id: str) -> dict[str, Any] | None:
        return self._states.get(agent_id)

    def increment_decide(self) -> None:
        self._metrics["total_decide_requests"] += 1

    def increment_fallback(self) -> None:
        self._metrics["total_fallbacks"] += 1

    def metrics(self) -> dict[str, int]:
        return {
            "total_observe_requests": self._metrics["total_observe_requests"],
            "total_decide_requests": self._metrics["total_decide_requests"],
            "total_fallbacks": self._metrics["total_fallbacks"],
        }


state_store = InMemoryStateStore()
