class AlertService:
    def evaluate(self, summary: dict) -> dict:
        alerts = []
        total_agents = int(summary.get("total_agents", 0) or 0)
        agents_needing_recovery = int(summary.get("agents_needing_recovery", 0) or 0)
        if total_agents > 0 and agents_needing_recovery / max(total_agents, 1) >= 0.2:
            alerts.append("recovery_ratio_high")
        if int(summary.get("active_agents", 0) or 0) == 0 and total_agents > 0:
            alerts.append("no_active_agents")
        return {
            "triggered": len(alerts) > 0,
            "alerts": alerts,
        }


alert_service = AlertService()
