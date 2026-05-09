import json
from typing import Any

from redis import Redis

from app.core.config import settings


class RedisStore:
    def __init__(self) -> None:
        self.client = Redis.from_url(settings.redis_url, decode_responses=True)
        self._metrics = {
            "total_observe_requests": 0,
            "total_decide_requests": 0,
            "total_fallbacks": 0,
            "total_profiles_saved": 0,
            "total_events_saved": 0,
            "total_learning_digests": 0,
            "total_learning_records": 0,
            "total_learning_issues": 0,
        }

    def _key(self, prefix: str, agent_id: str) -> str:
        return f"aia:{prefix}:{agent_id}"

    def _json_dumps(self, payload: dict[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=False)

    def save_state(self, agent_id: str, tick: int, state: dict) -> None:
        self.client.set(self._key("state", agent_id), self._json_dumps({"tick": tick, "state": state}))
        self._metrics["total_observe_requests"] += 1

    def get_state(self, agent_id: str):
        raw = self.client.get(self._key("state", agent_id))
        return json.loads(raw) if raw else None

    def save_profile(self, agent_id: str, profile: dict) -> None:
        self.client.set(self._key("profile", agent_id), self._json_dumps(profile))
        self._metrics["total_profiles_saved"] += 1

    def update_profile(self, agent_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        current = dict(self.get_profile(agent_id) or {"agent_id": agent_id})
        current.update(patch)
        current["agent_id"] = agent_id
        self.save_profile(agent_id, current)
        return current

    def get_profile(self, agent_id: str) -> dict:
        raw = self.client.get(self._key("profile", agent_id))
        return json.loads(raw) if raw else {}

    def has_agent(self, agent_id: str) -> bool:
        return agent_id in self.list_agent_ids() or agent_id in self.list_learning_ids()

    def delete_agent(self, agent_id: str) -> bool:
        existed = self.has_agent(agent_id)
        keys = [
            self._key("state", agent_id),
            self._key("profile", agent_id),
            self._key("events", agent_id),
            self._key("trace", agent_id),
            self._key("learning", agent_id),
        ]
        if keys:
            self.client.delete(*keys)
        return existed

    def save_event(self, agent_id: str, event: dict) -> None:
        key = self._key("events", agent_id)
        self.client.rpush(key, self._json_dumps(event))
        self.client.ltrim(key, -20, -1)
        self._metrics["total_events_saved"] += 1

    def get_recent_events(self, agent_id: str, limit: int = 10) -> list:
        rows = self.client.lrange(self._key("events", agent_id), -limit, -1)
        return [json.loads(row) for row in rows]

    def save_trace(self, agent_id: str, trace: dict) -> None:
        self.client.set(self._key("trace", agent_id), self._json_dumps(trace))

    def get_trace(self, agent_id: str) -> dict:
        raw = self.client.get(self._key("trace", agent_id))
        return json.loads(raw) if raw else {}

    def save_learning_state(self, agent_id: str, learning_state: dict) -> None:
        self.client.set(self._key("learning", agent_id), self._json_dumps(learning_state))

    def get_learning_state(self, agent_id: str) -> dict:
        raw = self.client.get(self._key("learning", agent_id))
        return json.loads(raw) if raw else {}

    def list_agent_ids(self) -> list[str]:
        ids = set()
        for prefix in ("state", "profile", "events", "trace"):
            marker = f"aia:{prefix}:"
            for key in self.client.scan_iter(f"{marker}*"):
                ids.add(str(key).replace(marker, "", 1))
        return sorted(ids)

    def list_learning_ids(self) -> list[str]:
        marker = "aia:learning:"
        return sorted(str(key).replace(marker, "", 1) for key in self.client.scan_iter(f"{marker}*"))

    def increment_decide(self) -> None:
        self._metrics["total_decide_requests"] += 1

    def increment_fallback(self) -> None:
        self._metrics["total_fallbacks"] += 1

    def increment_learning_digest(self, records: int, issues: int) -> None:
        self._metrics["total_learning_digests"] += 1
        self._metrics["total_learning_records"] += max(0, int(records or 0))
        self._metrics["total_learning_issues"] += max(0, int(issues or 0))

    def metrics(self) -> dict:
        return dict(self._metrics)
