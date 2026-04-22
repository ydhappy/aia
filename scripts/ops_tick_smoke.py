import json
import os
import urllib.request


def main() -> None:
    base_url = os.environ.get("AIA_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    api_key = os.environ.get("API_KEY", "")
    payload = {
        "profile": {
            "agent_id": "robot_smoke_ops",
            "role": "custom",
            "style": "balanced",
            "metadata": {"source": "ops_tick_smoke"},
        },
        "observe": {
            "agent_id": "robot_smoke_ops",
            "tick": 1,
            "state": {
                "hp": 91,
                "mp": 20,
                "x": 33400,
                "y": 32800,
                "map_id": 68,
                "can_teleport": False,
                "extras": {"level": 28, "robot_uid": 9901},
            },
        },
        "decide": {
            "agent_id": "robot_smoke_ops",
            "tick": 1,
            "state": {
                "hp": 91,
                "mp": 20,
                "x": 33400,
                "y": 32800,
                "map_id": 68,
                "can_teleport": False,
                "extras": {"level": 28, "robot_uid": 9901},
            },
        },
        "include_dashboard": True,
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        base_url + "/api/v1/robot/ops-tick",
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    if api_key:
        request.add_header("X-API-Key", api_key)
    with urllib.request.urlopen(request, timeout=5) as response:
        data = json.loads(response.read().decode("utf-8"))
    decision = data.get("decide_result") or {}
    args = decision.get("action_args") or {}
    print("OPS_TICK_OK=1")
    print("ACTION=%s" % decision.get("action"))
    print("ROUTE_ID=%s" % args.get("route_id"))
    print("CHECKLIST=%s" % data.get("checklist_status"))


if __name__ == "__main__":
    main()
