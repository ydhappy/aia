from app.models.request_models import AgentState
from app.services.policy_engine import policy_engine
from app.services.robot_ai_ops_service import robot_ai_ops_service
from app.services.store_factory import store


def test_ops_assessment_detects_local_area_over_level() -> None:
    state = AgentState(
        hp=88,
        mp=20,
        x=33085,
        y=32380,
        map_id=4,
        can_teleport=True,
        extras={
            "level": 10,
            "local_area_level": 17,
            "nearby_monster_max_level": 17,
            "actor_kind": "robot",
        },
    )
    assessment = robot_ai_ops_service.assess_state(state)
    assert assessment["severity"] == "high"
    assert assessment["should_retreat"] is True


def test_policy_uses_ops_risk_for_retreat() -> None:
    state = AgentState(
        hp=88,
        mp=20,
        x=33085,
        y=32380,
        map_id=4,
        can_teleport=True,
        target_id="mob_17",
        target_distance=3,
        inventory={},
        extras={
            "level": 10,
            "target_level": 17,
            "local_area_level": 17,
            "danger_hotspot": True,
        },
    )
    decision = policy_engine.decide(state)
    assert decision.action == "RETREAT"
    assert decision.action_args["nav_algorithm"] == "danger_retreat"
    assert decision.action_args["risk_score"] >= 55


def test_beginner_talking_island_field_does_not_over_retreat() -> None:
    state = AgentState(
        hp=96,
        mp=20,
        x=32513,
        y=33004,
        map_id=0,
        can_teleport=False,
        target_id="training_mob",
        target_distance=3,
        inventory={"infinite_healing_potion": 1},
        extras={
            "level": 1,
            "robot_level": 1,
            "local_area_level": 21,
            "target_level": 6,
            "nearby_monster_max_level": 14,
            "fresh_talking_island_start": True,
        },
    )

    assessment = robot_ai_ops_service.assess_state(state)
    decision = policy_engine.decide(state)

    assert assessment["severity"] != "high"
    assert assessment["should_retreat"] is False
    assert "beginner_training_leniency" in assessment["reasons"]
    assert decision.action in {"MOVE", "ATTACK"}


def test_aia_escape_policy_marks_under_attack_hp_pressure() -> None:
    state = AgentState(
        hp=69,
        mp=20,
        x=32611,
        y=32840,
        map_id=0,
        is_under_attack=True,
        safe_zone=False,
        must_use_hp_item=True,
        extras={"level": 20, "class_name": "knight", "robot_uid": 900},
    )

    assessment = robot_ai_ops_service.assess_state(state)

    assert any(reason.startswith("aia_escape_policy") for reason in assessment["reasons"])
    assert assessment["risk_score"] >= 50


def test_ops_assessment_detects_repeat_death_profile() -> None:
    state = AgentState(
        hp=82,
        mp=20,
        x=33094,
        y=32362,
        map_id=4,
        can_teleport=True,
        inventory={},
        extras={
            "level": 11,
            "learning_death_count": 3,
            "learning_caution": 5,
            "learning_confidence": 13,
            "recent_death_burst": 0,
        },
    )
    assessment = robot_ai_ops_service.assess_state(state)
    decision = policy_engine.decide(state)
    assert "repeat_death_profile:3/5" in assessment["reasons"]
    assert decision.action == "RETREAT"
    assert decision.action_args["nav_algorithm"] == "danger_retreat"


def test_policy_uses_available_potion_when_hp_below_95() -> None:
    state = AgentState(
        hp=94,
        mp=20,
        x=33094,
        y=32362,
        map_id=4,
        must_use_hp_item=True,
        inventory={"potion": 3},
    )
    decision = policy_engine.decide(state)
    assert decision.action == "USE_SKILL"
    assert decision.action_args["item"] == "potion"
    assert decision.reason == "hp_below_95_use_available_potion"


def test_policy_retreats_before_heal_on_critical_hp_risk() -> None:
    state = AgentState(
        hp=22,
        mp=20,
        x=33115,
        y=32296,
        map_id=4,
        can_teleport=True,
        must_use_hp_item=True,
        inventory={"potion": 10},
        extras={"level": 11, "learning_death_count": 1, "learning_caution": 5},
    )
    decision = policy_engine.decide(state)
    assert decision.action == "RETREAT"
    assert decision.action_args["use_hp_item_first"] is True
    assert decision.action_args["item"] == "potion"
    assert decision.reason.startswith("critical_hp_retreat_before_heal")


def test_policy_returns_diverse_navigation_when_no_target() -> None:
    state = AgentState(
        hp=90,
        mp=20,
        x=34000,
        y=32860,
        map_id=4,
        can_teleport=True,
        extras={"level": 30, "local_area_level": 20, "teleport_hunt_enabled": True},
    )
    decision = policy_engine.decide(state)
    assert decision.action == "MOVE"
    assert decision.action_args["nav_algorithm"] in {"teleport_hunt", "spawn_anchor", "frontier_roam"}
    assert decision.action_args["points"]
    assert decision.action_args["target_map_id"] == 4
    assert decision.action_args["server_validation"]["authoritative"] == "server"


def test_ops_navigation_points_are_deterministic_and_anti_clump_ready() -> None:
    state = AgentState(
        hp=90,
        mp=20,
        x=33400,
        y=32800,
        map_id=68,
        can_teleport=False,
        extras={"level": 28, "robot_uid": 1001},
    )
    first = robot_ai_ops_service.choose_navigation(state)
    second = robot_ai_ops_service.choose_navigation(state)
    assert first["points"] == second["points"]
    assert first["route_id"] == second["route_id"]
    assert first["spread_radius"] >= 10
    assert first["client_server_sync"]["aia_is_strategy_owner"] is True


def test_ops_uses_siege_attack_when_giran_war_is_active() -> None:
    state = AgentState(
        hp=91,
        mp=30,
        x=33620,
        y=32700,
        map_id=4,
        can_teleport=True,
        extras={
            "level": 52,
            "siege_active": True,
            "siege_offense": True,
            "siege_throne_x": 33631,
            "siege_throne_y": 32678,
            "siege_throne_map": 4,
        },
    )

    decision = policy_engine.decide(state, profile={"role": "siege_offense"})

    assert decision.action == "MOVE"
    assert decision.action_args["nav_algorithm"] == "siege_attack"
    assert decision.action_args["target_map_id"] == 4
    assert decision.action_args["points"][0]["map_id"] == 4


def test_ops_uses_dungeon_sweep_from_aia_baseline() -> None:
    state = AgentState(
        hp=92,
        mp=30,
        x=32750,
        y=32750,
        map_id=70,
        can_teleport=False,
        extras={"level": 38, "dungeon_map": True, "local_area_level": 34},
    )

    decision = policy_engine.decide(state)

    assert decision.action == "MOVE"
    assert decision.action_args["nav_algorithm"] == "dungeon_sweep"
    assert decision.action_args["mode"] == "corridor_sweep"


def test_dashboard_snapshot_contains_checklist() -> None:
    store.save_state("robot_dash", 1, {"hp": 90})
    snapshot = robot_ai_ops_service.dashboard_snapshot(["robot_dash"])
    assert snapshot.total_agents == 1
    assert snapshot.active_agents == 1
    assert snapshot.dependency_score > 0
    assert {item.key for item in snapshot.checklist} >= {"bridge", "dashboard", "navigation", "issues", "aia_default_baseline", "aia_top_profile", "log_cleanup"}
    assert snapshot.navigation_contract["anti_clump_rule"]
    assert snapshot.navigation_contract["bookless_rule"]
    assert snapshot.autonomy_baseline["no_db_required"] is True
    assert snapshot.cleanup_policy["talk_memories"] == "delete_after_digest_apply_when_last_message_was_learned"
    assert {gate["key"] for gate in snapshot.quality_gates} >= {"compile", "runtime", "fallback", "dashboard", "aia_top"}
