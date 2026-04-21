from typing import Any

import httpx

from app.core.config import settings


class LLMClient:
    def __init__(self) -> None:
        self.backend = settings.llm_backend.lower()
        self.base_url = settings.llm_base_url.rstrip("/")
        self.model = settings.llm_model
        self.timeout = settings.llm_timeout_seconds
        self.api_key = settings.llm_api_key
        self.provider = settings.llm_provider.lower()

    def health(self) -> str:
        if self.backend == "none":
            return "disabled"
        if self.backend == "hosted":
            return f"configured:{self.provider}"
        return "configured"

    def should_use_llm(self, state: dict[str, Any]) -> bool:
        extras = state.get("extras", {})
        return bool(extras.get("require_llm", False))

    def build_prompt(self, context: dict[str, Any]) -> str:
        return (
            "You are a lightweight MMORPG AI agent assistant. "
            "Return only one JSON object. "
            "Allowed actions: MOVE, ATTACK, USE_SKILL, RETREAT, PICKUP, IDLE. "
            "JSON schema: {\"action\": str, \"action_args\": object, \"confidence\": number, \"reason\": str}. "
            "Never return markdown. Never return explanations outside JSON. "
            f"Context: {context}"
        )

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _openai_compatible_request(self, client: httpx.Client, prompt: str) -> dict[str, Any] | None:
        response = client.post(
            f"{self.base_url}/v1/chat/completions",
            headers=self._headers(),
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Return exactly one JSON object with a single safe action.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
            },
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices", [])
        content = choices[0]["message"]["content"] if choices else ""
        return {"raw": content}

    def decide(self, context: dict[str, Any]) -> dict[str, Any] | None:
        if self.backend == "none":
            return None

        prompt = self.build_prompt(context)

        try:
            with httpx.Client(timeout=self.timeout) as client:
                if self.backend == "ollama":
                    response = client.post(
                        f"{self.base_url}/api/generate",
                        json={
                            "model": self.model,
                            "prompt": prompt,
                            "stream": False,
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                    return {"raw": data.get("response", "")}

                if self.backend == "llama.cpp":
                    return self._openai_compatible_request(client, prompt)

                if self.backend == "hosted":
                    return self._openai_compatible_request(client, prompt)
        except Exception:
            return None

        return None


llm_client = LLMClient()
