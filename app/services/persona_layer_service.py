class PersonaLayerService:
    def build(self, profile: dict | None = None) -> dict:
        profile = profile or {}
        metadata = profile.get("metadata", {}) or {}
        mbti = str(metadata.get("mbti", "balanced")).upper()
        generation = str(metadata.get("generation", "standard")).lower()
        speech_level = str(metadata.get("speech_level", "standard")).lower()
        relationship = str(metadata.get("relationship", "neutral")).lower()
        speech_mode = str(metadata.get("speech_mode", "standard")).lower()
        slang_level = str(metadata.get("slang_level", "none")).lower()
        meme_level = str(metadata.get("meme_level", "none")).lower()

        return {
            "mbti": mbti,
            "generation": generation,
            "speech_level": speech_level,
            "relationship": relationship,
            "speech_mode": speech_mode,
            "slang_level": slang_level,
            "meme_level": meme_level,
            "tone_bias": self._tone_bias(mbti, generation),
        }

    def _tone_bias(self, mbti: str, generation: str) -> str:
        if mbti in {"INTJ", "ISTJ", "INFJ"}:
            return "calm_precise"
        if mbti in {"ENTJ", "ESTJ", "ENFJ"}:
            return "directive_clear"
        if mbti in {"ENFP", "ESFP", "INFP"}:
            return "warm_expressive"
        if generation in {"mz", "genz", "millennial"}:
            return "light_direct"
        if generation in {"x", "boom"}:
            return "formal_stable"
        return "balanced"


persona_layer_service = PersonaLayerService()
