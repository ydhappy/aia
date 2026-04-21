class AlertPayloadService:
    def build(self, summary: dict, alerts: dict) -> dict:
        return {
            "summary": summary,
            "alerts": alerts.get("alerts", []),
            "triggered": bool(alerts.get("triggered", False)),
            "severity": "high" if "recovery_ratio_high" in alerts.get("alerts", []) else "normal",
        }


alert_payload_service = AlertPayloadService()
