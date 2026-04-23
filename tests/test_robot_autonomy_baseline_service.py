from app.models.request_models import AgentState
from app.services.robot_autonomy_baseline_service import robot_autonomy_baseline_service


def test_baseline_builds_profile_from_aia_baseline_only() -> None:
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
    assert profile["metadata"]["aia_autonomy_without_book_table"] is True
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


def test_baseline_loads_aia_top_profile() -> None:
    profile = robot_autonomy_baseline_service.load_top_profile(force=True)
    view = robot_autonomy_baseline_service.operator_view()

    assert profile["description"].startswith("AIA")
    assert view["summary"]["aia_top_zones"] >= 90
    assert view["summary"]["aia_party_spawn_groups"] == 10
    assert view["summary"]["aia_pickup_zones"] == 2


def test_baseline_can_select_aia_field_zone() -> None:
    state = AgentState(
        hp=90,
        mp=40,
        x=33449,
        y=32817,
        map_id=4,
        can_teleport=True,
        extras={"level": 32, "class_name": "knight", "robot_uid": 777},
    )

    zones = robot_autonomy_baseline_service._enabled_zones(robot_autonomy_baseline_service.load())
    matching = [
        zone for zone in zones
        if zone.get("source") == "aia_top"
        and zone.get("map_id") == state.map_id
        and zone.get("min_level", 0) <= 32 <= zone.get("max_level", 999)
    ]

    assert matching
