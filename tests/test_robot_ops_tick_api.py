from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_robot_ops_tick_combines_observe_decide_dashboard() -> None:
    payload = {
        "profile": {
            "agent_id": "robot_ops_1",
            "name": "테스트로봇",
            "role": "custom",
            "style": "balanced",
            "home_x": 33400,
            "home_y": 32800,
            "metadata": {"server": "sp163"},
        },
        "observe": {
            "agent_id": "robot_ops_1",
            "tick": 1,
            "state": {
                "hp": 92,
                "mp": 30,
                "x": 33400,
                "y": 32800,
                "map_id": 68,
                "can_teleport": False,
                "extras": {"level": 28, "robot_uid": 77},
            },
        },
        "decide": {
            "agent_id": "robot_ops_1",
            "tick": 1,
            "state": {
                "hp": 92,
                "mp": 30,
                "x": 33400,
                "y": 32800,
                "map_id": 68,
                "can_teleport": False,
                "extras": {"level": 28, "robot_uid": 77},
            },
        },
    }

    response = client.post("/api/v1/robot/ops-tick", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is True
    assert body["agent_id"] == "robot_ops_1"
    assert body["observe_result"]["accepted"] is True
    assert body["decide_result"]["action"] in {"MOVE", "IDLE"}
    assert body["dashboard"]["mode"] == "aia_first_server_minimal"
    assert body["autonomy_profile"]["metadata"]["aia_autonomy_without_book_table"] is True
    assert body["talk_suggestion"]["message"]
    assert body["cleanup_policy"]["action_logs"] == "delete_after_digest_apply"
    assert body["server_minimal_contract"]["portable"] is True
    if body["decide_result"]["action"] == "MOVE":
        assert body["decide_result"]["action_args"]["points"]
        assert body["decide_result"]["action_args"]["route_id"]
