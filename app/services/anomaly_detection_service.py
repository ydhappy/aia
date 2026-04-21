class AnomalyDetectionService:
    def detect(self, trace: dict, growth_state: dict | None = None) -> dict:
        growth_state = growth_state or {}
        anomalies = []

        risk_score = float(trace.get("risk_score", 0.0) or 0.0)
        final_reason = str(trace.get("final_reason", "") or "")
        growth_stage = growth_state.get("stage", "novice")

        # AgentGraph currently produces integer-like risk scores.
        # Use integer thresholds here so we do not over-trigger anomaly flags.
        if risk_score >= 5:
            anomalies.append("high_risk_behavior")
        if "fallback" in final_reason:
            anomalies.append("fallback_triggered")
        if growth_stage == "novice" and risk_score >= 3:
            anomalies.append("unstable_novice_behavior")

        return {
            "detected": len(anomalies) > 0,
            "anomalies": anomalies,
        }


anomaly_detection_service = AnomalyDetectionService()
