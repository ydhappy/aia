class TalkService:
    def build_talk(self, goal_state: dict, growth_state: dict, anomalies: dict, next_step: dict, persona: dict | None = None) -> dict:
        persona = persona or {}
        goal = goal_state.get("primary_goal", "idle")
        phase = next_step.get("phase") or next_step.get("mode") or "idle"
        stage = growth_state.get("stage", "novice")
        anomaly_list = anomalies.get("anomalies", []) if isinstance(anomalies, dict) else []
        tone_bias = persona.get("tone_bias", "balanced")
        speech_level = persona.get("speech_level", "standard")

        if "high_risk_behavior" in anomaly_list:
            base = "위험도가 높습니다. 안전 우선으로 전환합니다."
            return self._styled("warning", base, tone_bias, speech_level)
        if phase in {"return_base", "return_and_resume", "return_to_safe_zone"}:
            base = "정비를 위해 복귀합니다."
            return self._styled("neutral", base, tone_bias, speech_level)
        if phase in {"inventory_reset", "npc_interaction", "resupply"}:
            base = "보급과 정리를 진행합니다."
            return self._styled("neutral", base, tone_bias, speech_level)
        if goal == "party_support":
            base = "파티를 지원하면서 위치를 유지합니다."
            return self._styled("support", base, tone_bias, speech_level)
        if goal == "loot_and_farm":
            base = "자원 확보와 회수를 우선합니다."
            return self._styled("focus", base, tone_bias, speech_level)
        if stage in {"optimized", "expert"} and phase in {"combat_loop", "farm"}:
            base = "전투 효율을 높여 전진합니다."
            return self._styled("confident", base, tone_bias, speech_level)
        if stage == "novice":
            base = "안정적으로 상황을 확인하며 진행합니다."
            return self._styled("careful", base, tone_bias, speech_level)
        base = "현재 목표에 맞춰 행동을 이어갑니다."
        return self._styled("standard", base, tone_bias, speech_level)

    def _styled(self, tone: str, message: str, tone_bias: str, speech_level: str) -> dict:
        if tone_bias == "directive_clear":
            message = message.replace("합니다.", "하겠습니다.")
        elif tone_bias == "warm_expressive":
            message = message.replace("합니다.", "해볼게요.")
        elif tone_bias == "light_direct":
            message = message.replace("합니다.", "진행할게요.")
        elif tone_bias == "formal_stable":
            message = message.replace("합니다.", "진행하겠습니다.")

        if speech_level == "soft":
            message = message.replace(".", "요.") if message.endswith(".") else message
        elif speech_level == "brief":
            message = message.replace("현재 ", "")

        return {"tone": tone, "message": message, "tone_bias": tone_bias, "speech_level": speech_level}


talk_service = TalkService()
