import json
from typing import Any

from app.models.response_models import DecideResponse


class LLMParser:
    def parse_decision(self, raw: str) -> DecideResponse | None:
        if not raw:
            return None

        text = raw.strip()
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None

        try:
            payload = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None

        if not isinstance(payload, dict):
            return None

        try:
            return DecideResponse(
                action=payload.get("action", "IDLE"),
                action_args=payload.get("action_args", {}),
                confidence=float(payload.get("confidence", 0.3)),
                reason=str(payload.get("reason", "llm_generated_decision")),
                source="llm",
            )
        except Exception:
            return None


llm_parser = LLMParser()
