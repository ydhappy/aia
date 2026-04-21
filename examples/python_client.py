import json
from urllib import request


BASE_URL = "http://127.0.0.1:8000"


def post(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        BASE_URL + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=2) as resp:
        return json.loads(resp.read().decode("utf-8"))


profile_payload = {
    "agent_id": "bot_001",
    "name": "CollectorOne",
    "role": "collector",
    "style": "balanced",
    "patrol_points": [{"x": 100, "y": 200}, {"x": 110, "y": 210}],
    "preferred_skills": [],
    "banned_skills": [],
    "tags": ["farm"],
    "notes": ["prioritize rare loot"],
    "metadata": {"server": "main"},
}

event_payload = {
    "agent_id": "bot_001",
    "tick": 120,
    "event_type": "loot_detected",
    "severity": "low",
    "message": "rare drop seen",
    "data": {"item_id": "rare_sword"},
}

observe_payload = {
    "agent_id": "bot_001",
    "tick": 121,
    "state": {
        "hp": 90,
        "mp": 20,
        "x": 100,
        "y": 200,
        "map_id": 4,
        "heading": 2,
        "target_id": None,
        "target_distance": None,
        "target_hp": None,
        "is_under_attack": False,
        "nearby_enemies": 0,
        "nearby_allies": 1,
        "safe_zone": False,
        "can_teleport": True,
        "weight_percent": 40,
        "cooldowns": {},
        "inventory": {"potion": 3},
        "buffs": [],
        "debuffs": [],
        "aggro_targets": [],
        "extras": {},
    },
}

decide_payload = observe_payload

if __name__ == "__main__":
    print(post("/robot/profile", profile_payload))
    print(post("/robot/event", event_payload))
    print(post("/observe", observe_payload))
    print(post("/decide", decide_payload))
