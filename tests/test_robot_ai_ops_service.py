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


def test_dashboard_snapshot_contains_checklist() -> None:
    store.save_state("robot_dash", 1, {"hp": 90})
    snapshot = robot_ai_ops_service.dashboard_snapshot(["robot_dash"])
    assert snapshot.total_agents == 1
    assert snapshot.active_agents == 1
    assert snapshot.dependency_score > 0
    assert {item.key for item in snapshot.checklist} >= {"bridge", "dashboard", "navigation", "issues"}
