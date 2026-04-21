class RuntimeOverrides:
    def get_override(self, profile: dict, state: dict) -> dict:
        overrides = profile.get("metadata", {}).get("overrides", {})
        map_id = str(state.get("map_id")) if state.get("map_id") is not None else None

        map_overrides = overrides.get("maps", {}) if isinstance(overrides, dict) else {}
        selected = map_overrides.get(map_id, {}) if map_id else {}
        return {
            "map_id": map_id,
            "override": selected,
        }


runtime_overrides = RuntimeOverrides()
