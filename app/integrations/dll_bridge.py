from __future__ import annotations

from typing import Any

import httpx


class RuntimeBridge:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", api_key: str = "change-me") -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def is_loaded(self) -> bool:
        return True

    def call_bool(self, func_name: str, *args: Any) -> bool:
        result = self.call_json(func_name, *args)
        return bool(result.get("ok", False)) if isinstance(result, dict) else bool(result)

    def call_int(self, func_name: str, *args: Any) -> int:
        result = self.call_json(func_name, *args)
        if isinstance(result, dict):
            value = result.get("value", -1)
            return int(value) if isinstance(value, (int, float, str)) else -1
        return int(result) if isinstance(result, (int, float, str)) else -1

    def call_str(self, func_name: str, *args: Any) -> str:
        result = self.call_json(func_name, *args)
        if isinstance(result, dict):
            return str(result.get("value", ""))
        return str(result)

    def call_json(self, func_name: str, *args: Any) -> dict:
        payload = {"function": func_name, "args": list(args)}
        headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}
        with httpx.Client(timeout=5.0) as client:
            response = client.post(f"{self.base_url}/bridge/runtime-call", headers=headers, json=payload)
            if response.status_code >= 400:
                return {"ok": False, "value": None, "error": response.text}
            try:
                return response.json()
            except Exception:
                return {"ok": False, "value": None, "error": "invalid_json"}


# Backward-compatible symbol name retained for migration safety.
dll_bridge = RuntimeBridge()
