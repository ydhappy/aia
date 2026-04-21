class FailureAnalysisService:
    def analyze(self, feedback: dict) -> list[str]:
        tags = []
        outcome = feedback.get("outcome")
        action = feedback.get("action")
        context = feedback.get("context", {}) or {}

        if outcome == "failure":
            tags.append("generic_failure")
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
