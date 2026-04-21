import json
import os

import httpx


def main() -> None:
    base_url = os.environ.get("AIA_BASE_URL", "http://127.0.0.1:8000")
    api_key = os.environ.get("AIA_API_KEY", "change-me")
    raw = os.environ.get("AIA_AGENT_IDS", "")
    agent_ids = [item.strip() for item in raw.split(",") if item.strip()]
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    with httpx.Client(timeout=30.0) as client:
        response = client.post(f"{base_url}/ops/scheduler/run", headers=headers, content=json.dumps(agent_ids))
        response.raise_for_status()
        print(response.text)


if __name__ == "__main__":
    main()
