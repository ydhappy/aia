class MetaPolicyService:
    def select_strategy(self, profile: dict, growth_state: dict, anomalies: dict) -> dict:
        role = profile.get("role", "custom")
        stage = growth_state.get("stage", "novice")
        detected = anomalies.get("detected", False)

        if detected:
            return {"strategy": "stability_first", "style": "defensive", "role": role}
        if stage == "expert":
            return {"strategy": "efficiency_first", "style": "aggressive", "role": role}
        if stage == "optimized":
            return {"strategy": "balanced_optimized", "style": "balanced", "role": role}
        return {"strategy": "safe_progression", "style": "defensive", "role": role}


meta_policy_service = MetaPolicyService()
