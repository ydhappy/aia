from app.models.request_models import AgentState
from app.services.robot_autonomy_baseline_service import robot_autonomy_baseline_service


def test_baseline_builds_profile_without_robot_book_or_talk_table() -> None:
    state = AgentState(
        hp=91,
        mp=40,
        x=33400,
        y=32800,
        map_id=68,
        extras={"level": 31, "class_name": "knight", "robot_uid": 501},
    )

    profile = robot_autonomy_baseline_service.resolve_profile("robot_501", state, {}, {})
    talk = robot_autonomy_baseline_service.build_talk_suggestion("robot_501", state, profile, {}, {})

    assert profile["role"] == "tank"
    assert profile["metadata"]["no_robot_book_required"] is True
    assert profile["metadata"]["no_talk_table_required"] is True
    assert profile["patrol_points"]
    assert talk["message"]
    assert talk["no_talk_table_required"] is True


def test_baseline_uses_operator_overrides_from_profile_metadata() -> None:
    state = AgentState(
        hp=88,
        mp=20,
        x=32600,
        y=32800,
        map_id=0,
        extras={"level": 7, "class_name": "elf", "robot_uid": 502},
    )
    profile = {
        "agent_id": "robot_502",
        "role": "custom",
        "metadata": {
            "autonomy_overrides": {
                "style": "aggressive",
                "patrol_points": [{"x": 1, "y": 2, "map_id": 3, "weight": 100}],
            }
        },
    }

    resolved = robot_autonomy_baseline_service.resolve_profile("robot_502", state, profile, {})

    assert resolved["role"] == "scout"
    assert resolved["style"] == "aggressive"
    assert resolved["patrol_points"][0]["map_id"] == 3


def test_baseline_prefers_learned_safe_zone_when_confident() -> None:
    state = AgentState(
        hp=90,
        mp=20,
        x=33000,
        y=33000,
        map_id=4,
        can_teleport=True,
        extras={
            "level": 25,
            "learning_preferred_x": 33111,
            "learning_preferred_y": 32222,
            "learning_preferred_map": 4,
            "learning_confidence": 8,
            "learning_caution": 2,
            "learning_roam_radius": 33,
        },
    )

    zone = robot_autonomy_baseline_service.select_hunt_zone(state, {}, {})

    assert zone["id"] == "aia_learned_preferred"
    assert zone["x"] == 33111
    assert zone["radius"] == 33
