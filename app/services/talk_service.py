class TalkService:
    def build_talk(self, goal_state: dict, growth_state: dict, anomalies: dict, next_step: dict) -> dict:
        goal = goal_state.get("primary_goal", "idle")
        phase = next_step.get("phase") or next_step.get("mode") or "idle"
        stage = growth_state.get("stage", "novice")
        anomaly_list = anomalies.get("anomalies", []) if isinstance(anomalies, dict) else []

        if "high_risk_behavior" in anomaly_list:
            return {"tone": "warning", "message": "위험도가 높습니다. 안전 우선으로 전환합니다."}
        if phase in {"return_base", "return_and_resume", "return_to_safe_zone"}:
            return {"tone": "neutral", "message": "정비를 위해 복귀합니다."}
        if phase in {"inventory_reset", "npc_interaction", "resupply"}:
            return {"tone": "neutral", "message": "보급과 정리를 진행합니다."}
        if goal == "party_support":
            return {"tone": "support", "message": "파티를 지원하면서 위치를 유지합니다."}
        if goal == "loot_and_farm":
            return {"tone": "focus", "message": "자원 확보와 회수를 우선합니다."}
        if stage in {"optimized", "expert"} and phase in {"combat_loop", "farm"}:
            return {"tone": "confident", "message": "전투 효율을 높여 전진합니다."}
        if stage == "novice":
            return {"tone": "careful", "message": "안정적으로 상황을 확인하며 진행합니다."}
        return {"tone": "standard", "message": "현재 목표에 맞춰 행동을 이어갑니다."}


talk_service = TalkService()
