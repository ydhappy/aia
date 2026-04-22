class FailureAnalysisService:
    def analyze(self, feedback: dict) -> list[str]:
        tags = []
        outcome = feedback.get("outcome")
        action = feedback.get("action")
        context = feedback.get("context", {}) or {}
        source_action = str(context.get("source_action", "")).lower()

        if outcome == "failure":
            tags.append("generic_failure")
        if action == "SURVIVE" and outcome == "failure":
            tags.append("survival_failure")
            tags.append("retreat_timing_bad")
        if source_action in {"dead", "death_drop"}:
            tags.append("dangerous_hunt_area")
        if source_action in {"stall_autofix", "collision_relief"}:
            tags.append("path_blocked")
            tags.append("movement_stall")
        if source_action == "shop_supply":
            tags.append("inventory_management_bad")
        if action == "MOVE" and context.get("blocked"):
            tags.append("path_blocked")
        if action == "ATTACK" and context.get("invalid_target"):
            tags.append("invalid_target")
        if action == "RETREAT" and context.get("late_retreat"):
            tags.append("retreat_timing_bad")
        if context.get("overweight"):
            tags.append("inventory_management_bad")
        return tags


failure_analysis_service = FailureAnalysisService()
