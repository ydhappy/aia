from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.live_json import LiveJsonFile
from app.models.request_models import AgentState
from app.services.server_context_service import server_context_service


class RobotAutonomyBaselineService:
    def __init__(self) -> None:
        self.config_path = Path(__file__).resolve().parents[1] / "config" / "robot_autonomy_defaults.json"
        self.top_profile_path = Path(__file__).resolve().parents[1] / "config" / "aia_robot_top_profile.json"
        self.config_file = LiveJsonFile(self.config_path, fallback=self._fallback_config)
        self.top_profile_file = LiveJsonFile(self.top_profile_path, fallback=lambda: {})

    def load(self, force: bool = False) -> dict[str, Any]:
        return self.config_file.load(force=force)

    def save_operator_config(self, config: dict[str, Any]) -> dict[str, Any]:
        safe_config = config if isinstance(config, dict) else self._fallback_config()
        return self.config_file.save(safe_config)

    def operator_view(self) -> dict[str, Any]:
        config = self.load()
        top_profile = self.load_top_profile()
        top_zones = self._top_profile_zones(top_profile)
        server_context = server_context_service.snapshot()
        world_guides = server_context.get("world_guides", {}) if isinstance(server_context, dict) else {}
        return {
            "config_path": str(self.config_path),
            "top_profile_path": str(self.top_profile_path),
            "live_reload": {
                "enabled": True,
                "config": self.config_file.info(),
                "top_profile": self.top_profile_file.info(),
            },
            "no_db_required": True,
            "operator_editable": True,
            "server_context": server_context,
            "summary": {
                "hunt_zones": len(self._enabled_zones(config)),
                "class_profiles": len(config.get("class_profiles", {}) or {}),
                "talk_topics": len(config.get("talk_templates", {}) or {}),
                "aia_top_zones": len(top_zones),
                "aia_db_hunt_zones": int(world_guides.get("hunt_zone_count", 0) or 0),
                "aia_db_siege_guides": int(world_guides.get("siege_guide_count", 0) or 0),
                "aia_party_spawn_groups": len(top_profile.get("party_spawn_groups", {}) or {}),
                "aia_pvp_zones": len(top_profile.get("pvp_zones", []) or []),
                "aia_pickup_zones": len(top_profile.get("pickup_zones", []) or []),
            },
            "config": config,
            "aia_top_profile": {
                "loaded": bool(top_profile),
                "behavior_constants": top_profile.get("behavior_constants", {}),
            },
        }

    def resolve_profile(
        self,
        agent_id: str,
        state: AgentState | None,
        profile: dict[str, Any] | None = None,
        learning_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        config = self.load()
        profile = dict(profile or {})
        learning_state = learning_state or {}
        extras = state.extras if state is not None else {}
        defaults = config.get("defaults", {}) if isinstance(config.get("defaults"), dict) else {}
        class_key = self._class_key(extras)
        class_profile = self._class_profile(config, class_key)
        zone = self.select_hunt_zone(state, profile, learning_state)
        resolved = dict(profile)
        role = resolved.get("role")
        if not role or role == "custom":
            resolved["role"] = class_profile.get("role") or "dealer"
        resolved.setdefault("agent_id", agent_id)
        resolved.setdefault("style", class_profile.get("style") or defaults.get("style") or "balanced")
        if state is not None and state.hp <= 45:
            resolved["style"] = "defensive"
        resolved.setdefault("name", agent_id)
        resolved.setdefault("home_x", zone.get("x") if zone else (state.x if state is not None else None))
        resolved.setdefault("home_y", zone.get("y") if zone else (state.y if state is not None else None))
        if not resolved.get("patrol_points"):
            resolved["patrol_points"] = self.build_patrol_points(state, zone)
        metadata = dict(resolved.get("metadata") or {})
        metadata["autonomy_source"] = "aia_default_baseline"
        metadata["operator_config_path"] = str(self.config_path)
        metadata["aia_top_profile_path"] = str(self.top_profile_path)
        metadata["aia_top_profile_loaded"] = bool(self.load_top_profile())
        metadata["aia_autonomy_without_book_table"] = True
        metadata["no_talk_table_required"] = True
        metadata["class_key"] = class_key
        if zone:
            metadata["hunt_zone_id"] = zone.get("id")
            metadata["hunt_zone_name"] = zone.get("name")
            metadata["hunt_zone_type"] = zone.get("type")
        resolved["metadata"] = metadata
        overrides = self._operator_overrides(profile)
        if overrides:
            resolved = self._deep_merge(resolved, overrides)
        return resolved

    def select_hunt_zone(self, state: AgentState | None, profile: dict[str, Any] | None = None, learning_state: dict[str, Any] | None = None) -> dict[str, Any]:
        config = self.load()
        profile = profile or {}
        learning_state = learning_state or {}
        extras = state.extras if state is not None else {}
        level = self._to_int(extras.get("robot_level", extras.get("level")), 1)
        current_map = state.map_id if state is not None else None
        learned_zone = self._learned_zone(state, learning_state)
        if learned_zone:
            return learned_zone
        zones = self._enabled_zones(config)
        suitable = [zone for zone in zones if self._to_int(zone.get("min_level"), 1) <= level <= self._to_int(zone.get("max_level"), 999)]
        same_map = [zone for zone in suitable if current_map is not None and self._to_int(zone.get("map_id"), -1) == current_map]
        candidates = same_map or suitable or zones
        if candidates:
            seed = self._seed(str(profile.get("agent_id") or ""), state, "hunt_zone")
            return dict(candidates[seed % len(candidates)])
        if state is None:
            return {}
        return {"id": "current_position_generated", "name": "AIA 현재 좌표 임시 사냥 기준", "type": "generated", "map_id": state.map_id, "x": state.x, "y": state.y, "min_level": 1, "max_level": 999, "radius": self._to_int(config.get("defaults", {}).get("roam_radius"), 22), "teleport": bool(state.can_teleport), "enabled": True}

    def build_patrol_points(self, state: AgentState | None, zone: dict[str, Any] | None) -> list[dict[str, int]]:
        if state is None and not zone:
            return []
        zone = zone or {}
        map_id = self._to_int(zone.get("map_id"), state.map_id if state is not None and state.map_id is not None else 0)
        base_x = self._to_int(zone.get("x"), state.x if state is not None else 0)
        base_y = self._to_int(zone.get("y"), state.y if state is not None else 0)
        radius = max(6, self._to_int(zone.get("radius"), 22))
        seed = self._seed(str(zone.get("id") or ""), state, "patrol")
        vectors = [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (-1, 1), (-1, -1), (1, -1)]
        points: list[dict[str, int]] = []
        for index in range(4):
            dx, dy = vectors[(seed + index * 2) % len(vectors)]
            spread = radius + ((seed // max(1, index + 1)) % max(4, radius // 2))
            points.append({"x": base_x + dx * spread, "y": base_y + dy * spread, "map_id": map_id, "weight": 100 - index * 12})
        return points

    def build_talk_suggestion(self, agent_id: str, state: AgentState | None, profile: dict[str, Any] | None = None, learning_state: dict[str, Any] | None = None, assessment: dict[str, Any] | None = None) -> dict[str, Any]:
        config = self.load()
        profile = profile or {}
        learning_state = learning_state or {}
        assessment = assessment or {}
        templates = self._merged_talk_templates(config)
        topic = self._talk_topic(state, learning_state, assessment)
        candidates = templates.get(topic) or templates.get("hunt") or ["상황을 보고 다음 행동을 정하겠습니다."]
        seed = self._seed(agent_id, state, topic)
        message = str(candidates[seed % len(candidates)]).strip() or "상황을 보고 다음 행동을 정하겠습니다."
        defaults = config.get("defaults", {}) if isinstance(config.get("defaults"), dict) else {}
        tone = (profile.get("metadata", {}).get("talk_tone") if isinstance(profile.get("metadata"), dict) else None) or profile.get("talk_tone") or defaults.get("talk_tone") or "중립"
        return {"topic": topic, "tone": tone, "message": message, "source": "aia_default_talk" if not learning_state.get("talk_stats") else "aia_learned_talk_bias", "no_talk_table_required": True, "preferred_talk_topic": learning_state.get("preferred_talk_topic")}

    def cleanup_policy(self) -> dict[str, Any]:
        return {"action_logs": "delete_after_digest_apply", "talk_memories": "delete_after_digest_apply_when_last_message_was_learned", "issue_logs": "keep_until_resolved", "aia_memory": "keep_in_state_store_or_redis"}

    def load_top_profile(self, force: bool = False) -> dict[str, Any]:
        return self.top_profile_file.load(force=force)

    def _enabled_zones(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        zones = config.get("hunt_zones", [])
        merged: list[dict[str, Any]] = []
        if isinstance(zones, list):
            merged.extend(dict(zone) for zone in zones if isinstance(zone, dict) and zone.get("enabled", True))
        merged.extend(self._top_profile_zones(self.load_top_profile()))
        merged.extend(server_context_service.world_hunt_zones())
        return merged

    def _top_profile_zones(self, profile: dict[str, Any]) -> list[dict[str, Any]]:
        if not isinstance(profile, dict) or not profile:
            return []
        zones: list[dict[str, Any]] = []
        raw_zones = profile.get("hunt_zones", [])
        if isinstance(raw_zones, list):
            zones.extend(dict(zone) for zone in raw_zones if isinstance(zone, dict) and zone.get("enabled", True))
        groups = profile.get("hunt_zone_groups", [])
        if isinstance(groups, list):
            for group in groups:
                if not isinstance(group, dict) or not group.get("enabled", True):
                    continue
                anchors = group.get("anchors", [])
                if not isinstance(anchors, list):
                    continue
                for index, anchor in enumerate(anchors, start=1):
                    if not isinstance(anchor, list) or len(anchor) < 4:
                        continue
                    x = self._to_int(anchor[0], 0)
                    y = self._to_int(anchor[1], 0)
                    map_id = self._to_int(anchor[2], 0)
                    min_level = self._to_int(anchor[3], 1)
                    zones.append({"id": f"{group.get('id', 'aia_zone')}_{index:03d}", "name": f"{group.get('name', 'AIA 권역')}#{index:03d}", "type": group.get("type", "field"), "map_id": map_id, "x": x, "y": y, "min_level": min_level, "max_level": self._to_int(group.get("max_level"), max(min_level + 24, 30)), "radius": self._to_int(group.get("radius"), 36), "teleport": bool(group.get("teleport", True)), "enabled": True, "source": "aia_top"})
        return zones

    def _merged_talk_templates(self, config: dict[str, Any]) -> dict[str, list[str]]:
        merged: dict[str, list[str]] = {}
        base = config.get("talk_templates", {}) if isinstance(config.get("talk_templates"), dict) else {}
        top = self.load_top_profile().get("talk_templates", {})
        for source in (base, top if isinstance(top, dict) else {}):
            for key, value in source.items():
                if not isinstance(value, list):
                    continue
                bucket = merged.setdefault(str(key), [])
                for item in value:
                    text = str(item).strip()
                    if text and text not in bucket:
                        bucket.append(text)
        return merged

    def _learned_zone(self, state: AgentState | None, learning_state: dict[str, Any]) -> dict[str, Any]:
        if state is None:
            return {}
        extras = state.extras or {}
        confidence = self._to_int(extras.get("learning_confidence"), 0)
        caution = self._to_int(extras.get("learning_caution"), 0)
        x = self._to_int(extras.get("learning_preferred_x"), 0)
        y = self._to_int(extras.get("learning_preferred_y"), 0)
        map_id = self._to_int(extras.get("learning_preferred_map"), 0)
        if x > 0 and y > 0 and confidence >= caution:
            return {"id": "aia_learned_preferred", "name": "AIA 학습 선호 사냥터", "type": "learned", "map_id": map_id if map_id > 0 else state.map_id, "x": x, "y": y, "min_level": 1, "max_level": 999, "radius": max(12, self._to_int(extras.get("learning_roam_radius"), 24)), "teleport": bool(state.can_teleport), "enabled": True}
        preferred_by_map = learning_state.get("preferred_action_by_map") or {}
        if isinstance(preferred_by_map, dict) and str(state.map_id) in preferred_by_map:
            return {"id": "aia_map_learning_anchor", "name": "AIA 맵별 학습 앵커", "type": "learned", "map_id": state.map_id, "x": state.x, "y": state.y, "min_level": 1, "max_level": 999, "radius": 28, "teleport": bool(state.can_teleport), "enabled": True}
        return {}

    def _talk_topic(self, state: AgentState | None, learning_state: dict[str, Any], assessment: dict[str, Any]) -> str:
        if assessment.get("severity") == "high":
            return "warning"
        if state is not None and state.safe_zone:
            return "town"
        if state is not None and state.target_id:
            return "combat"
        preferred = str(learning_state.get("preferred_talk_topic") or "").strip()
        return preferred if preferred in {"warning", "hunt", "combat", "town", "growth"} else "hunt"

    def _class_profile(self, config: dict[str, Any], class_key: str) -> dict[str, Any]:
        profiles = config.get("class_profiles", {}) if isinstance(config.get("class_profiles"), dict) else {}
        value = profiles.get(class_key) or profiles.get("default") or {}
        return value if isinstance(value, dict) else {}

    def _class_key(self, extras: dict[str, Any]) -> str:
        raw = str(extras.get("class_name") or extras.get("class") or "").strip().lower()
        if raw in {"royal", "prince", "princess", "군주"}:
            return "royal"
        if raw in {"knight", "기사"}:
            return "knight"
        if raw in {"elf", "요정"}:
            return "elf"
        if raw in {"wizard", "mage", "마법사"}:
            return "wizard"
        class_type = self._to_int(extras.get("class_type"), -1)
        return {0: "royal", 1: "knight", 2: "elf", 3: "wizard"}.get(class_type, "default")

    def _operator_overrides(self, profile: dict[str, Any]) -> dict[str, Any]:
        metadata = profile.get("metadata") if isinstance(profile, dict) else {}
        if not isinstance(metadata, dict):
            return {}
        overrides = metadata.get("autonomy_overrides") or metadata.get("operator_overrides") or {}
        return overrides if isinstance(overrides, dict) else {}

    def _deep_merge(self, base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
        result = dict(base)
        for key, value in update.items():
            result[key] = self._deep_merge(result[key], value) if isinstance(value, dict) and isinstance(result.get(key), dict) else value
        return result

    def _seed(self, agent_id: str, state: AgentState | None, salt: str) -> int:
        raw = f"{salt}:{agent_id}:{state.x if state is not None else 0}:{state.y if state is not None else 0}:{state.map_id if state is not None else 0}:{state.extras.get('robot_uid', '') if state is not None else ''}"
        seed = 0
        for ch in raw:
            seed = (seed * 131 + ord(ch)) & 0x7FFFFFFF
        return seed

    def _to_int(self, value: Any, default: int = 0) -> int:
        try:
            if value is None or value == "":
                return default
            return int(value)
        except Exception:
            return default

    def _fallback_config(self) -> dict[str, Any]:
        return {"version": 0, "description": "AIA built-in fallback config", "defaults": {"style": "balanced", "roam_radius": 22, "talk_tone": "중립"}, "class_profiles": {"default": {"role": "dealer", "style": "balanced"}}, "hunt_zones": [], "talk_templates": {"hunt": ["상황을 보고 다음 행동을 정하겠습니다."]}}


robot_autonomy_baseline_service = RobotAutonomyBaselineService()

__all__ = ["RobotAutonomyBaselineService", "robot_autonomy_baseline_service"]
