class TalkService:
    def build_talk(self, goal_state: dict, growth_state: dict, anomalies: dict, next_step: dict, persona: dict | None = None) -> dict:
        persona = persona or {}
        goal = goal_state.get("primary_goal", "idle")
        phase = next_step.get("phase") or next_step.get("mode") or "idle"
        stage = growth_state.get("stage", "novice")
        anomaly_list = anomalies.get("anomalies", []) if isinstance(anomalies, dict) else []
        tone_bias = persona.get("tone_bias", "balanced")
        speech_level = persona.get("speech_level", "standard")
        speech_mode = persona.get("speech_mode", "standard")
        slang_level = persona.get("slang_level", "none")
        meme_level = persona.get("meme_level", "none")

        if "high_risk_behavior" in anomaly_list:
            base = "위험도가 높습니다. 안전 우선으로 전환합니다."
            return self._styled("warning", base, tone_bias, speech_level, speech_mode, slang_level, meme_level)
        if phase in {"return_base", "return_and_resume", "return_to_safe_zone"}:
            base = "정비를 위해 복귀합니다."
            return self._styled("neutral", base, tone_bias, speech_level, speech_mode, slang_level, meme_level)
        if phase in {"inventory_reset", "npc_interaction", "resupply"}:
            base = "보급과 정리를 진행합니다."
            return self._styled("neutral", base, tone_bias, speech_level, speech_mode, slang_level, meme_level)
        if goal == "party_support":
            base = "파티를 지원하면서 위치를 유지합니다."
            return self._styled("support", base, tone_bias, speech_level, speech_mode, slang_level, meme_level)
        if goal == "loot_and_farm":
            base = "자원 확보와 회수를 우선합니다."
            return self._styled("focus", base, tone_bias, speech_level, speech_mode, slang_level, meme_level)
        if stage in {"optimized", "expert"} and phase in {"combat_loop", "farm"}:
            base = "전투 효율을 높여 전진합니다."
            return self._styled("confident", base, tone_bias, speech_level, speech_mode, slang_level, meme_level)
        if stage == "novice":
            base = "안정적으로 상황을 확인하며 진행합니다."
            return self._styled("careful", base, tone_bias, speech_level, speech_mode, slang_level, meme_level)
        base = "현재 목표에 맞춰 행동을 이어갑니다."
        return self._styled("standard", base, tone_bias, speech_level, speech_mode, slang_level, meme_level)

    def _styled(self, tone: str, message: str, tone_bias: str, speech_level: str, speech_mode: str, slang_level: str, meme_level: str) -> dict:
        if tone_bias == "directive_clear":
            message = message.replace("합니다.", "하겠습니다.")
        elif tone_bias == "warm_expressive":
            message = message.replace("합니다.", "해볼게요.")
        elif tone_bias == "light_direct":
            message = message.replace("합니다.", "진행할게요.")
        elif tone_bias == "formal_stable":
            message = message.replace("합니다.", "진행하겠습니다.")

        message = self._apply_speech_mode(message, speech_mode)
        message = self._apply_speech_level(message, speech_level)
        message = self._apply_slang(message, slang_level)
        message = self._apply_meme(message, meme_level, tone)

        return {
            "tone": tone,
            "message": message,
            "tone_bias": tone_bias,
            "speech_level": speech_level,
            "speech_mode": speech_mode,
            "slang_level": slang_level,
            "meme_level": meme_level,
        }

    def _apply_speech_mode(self, message: str, speech_mode: str) -> str:
        if speech_mode == "banmal":
            return (
                message.replace("합니다.", "해.")
                .replace("하겠습니다.", "할게.")
                .replace("해볼게요.", "해볼게.")
                .replace("진행할게요.", "진행할게.")
                .replace("진행하겠습니다.", "진행할게.")
            )
        if speech_mode == "semi_formal":
            return (
                message.replace("합니다.", "해요.")
                .replace("하겠습니다.", "할게요.")
                .replace("진행하겠습니다.", "진행할게요.")
            )
        if speech_mode == "half_honorific":
            return (
                message.replace("합니다.", "할게요.")
                .replace("진행하겠습니다.", "진행할게요.")
            )
        return message

    def _apply_speech_level(self, message: str, speech_level: str) -> str:
        if speech_level == "soft":
            return message.replace("해.", "해요.").replace("할게.", "할게요.")
        if speech_level == "brief":
            return message.replace("현재 ", "").replace("안정적으로 ", "")
        return message

    def _apply_slang(self, message: str, slang_level: str) -> str:
        if slang_level == "light":
            return message.replace("진행", "가동").replace("확인", "체크")
        if slang_level == "high":
            return (
                message.replace("진행", "돌림")
                .replace("확인", "체크")
                .replace("복귀", "귀환")
            )
        return message

    def _apply_meme(self, message: str, meme_level: str, tone: str) -> str:
        if meme_level == "light":
            if tone == "confident":
                return message + " 가보자고."
            if tone == "warning":
                return message + " 분위기 심상치 않습니다."
        if meme_level == "high":
            if tone == "confident":
                return message + " 이건 못 참죠."
            if tone == "warning":
                return message + " 지금은 선 넘기 전에 빠집니다."
            if tone == "focus":
                return message + " 효율 챙깁니다."
        return message


talk_service = TalkService()
