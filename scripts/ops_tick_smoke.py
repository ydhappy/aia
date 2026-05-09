import json
import os
import sys
import urllib.error
import urllib.request


BASE_URL = os.environ.get("AIA_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
API_KEY = os.environ.get("API_KEY", "")


def post_json(path: str, payload: dict) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        BASE_URL + path,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8", "Accept": "application/json"},
        method="POST",
    )
    if API_KEY:
        request.add_header("X-API-Key", API_KEY)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw or "{}")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError("HTTP %s %s failed: %s" % (exc.code, path, raw))
    except urllib.error.URLError as exc:
        raise RuntimeError("AIA server not reachable at %s: %s" % (BASE_URL, exc))
    except json.JSONDecodeError as exc:
        raise RuntimeError("AIA returned non-JSON response from %s: %s" % (path, exc))


def main() -> None:
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
    data = post_json("/api/v1/robot/ops-tick", payload)
    decision = data.get("decide_result") or {}
    args = decision.get("action_args") or {}
    profile = data.get("autonomy_profile") or {}
    metadata = profile.get("metadata") or {}
    talk = data.get("talk_suggestion") or {}
    cleanup = data.get("cleanup_policy") or {}
    print("OPS_TICK_OK=1")
    print("ACTION=%s" % decision.get("action"))
    print("ROUTE_ID=%s" % args.get("route_id"))
    print("CHECKLIST=%s" % data.get("checklist_status"))
    print("NO_DB_BASELINE=%s" % metadata.get("no_robot_book_required"))
    print("HUNT_ZONE=%s" % metadata.get("hunt_zone_id"))
    print("TALK=%s" % talk.get("message"))
    print("TALK_CLEANUP=%s" % cleanup.get("talk_memories"))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("OPS_TICK_SMOKE_FAILED=%s" % exc, file=sys.stderr)
        raise
