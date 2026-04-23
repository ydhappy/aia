from app.models.request_models import RobotActionRecord, RobotLearningDigestRequest, RobotTalkMemoryRecord
from app.models.request_models import AgentState
from app.services.policy_engine import policy_engine
from app.services.robot_learning_digest_service import robot_learning_digest_service
from app.services.store_factory import store


def test_learning_digest_applies_feedback_and_returns_delete_uids() -> None:
    request = RobotLearningDigestRequest(
        server_name="test",
        tick=1,
        records=[
            RobotActionRecord(
                uid=101,
                agent_id="robot_1",
                robot_uid=1,
                object_id=9001,
                name="테스트로봇",
                action_type="aia_control",
                detail="MOVE:approach:123|confidence=0.84",
                loc_x=10,
                loc_y=20,
                loc_map=4,
                created_at=1,
            )
        ],
    )
    response = robot_learning_digest_service.apply_digest(request)
    learning = store.get_learning_state("robot_1")
    growth = store.get_learning_state("growth::robot_1")
    assert response.processed_records == 1
    assert response.delete_uids == [101]
    assert response.cleanup_policy["action_logs"] == "delete_after_digest_apply"
    assert learning["preferred_action"] == "MOVE"
    assert growth["stage"] in {"novice", "stable", "optimized", "expert"}


def test_learning_digest_detects_supply_and_talk_issues() -> None:
    request = RobotLearningDigestRequest(
        server_name="test",
        tick=2,
        records=[
            RobotActionRecord(
                uid=102,
                agent_id="robot_2",
                robot_uid=2,
                action_type="shop_supply",
                detail="healing_potion",
            ),
            RobotActionRecord(
                uid=103,
                agent_id="robot_2",
                robot_uid=2,
                action_type="robot_chat",
                detail="대상|",
            ),
        ],
        talk_memories=[
            RobotTalkMemoryRecord(
                robot_uid=2,
                agent_id="robot_2",
                target_name="유저",
                target_kind="pc",
                familiarity=30,
                conversation_count=3,
                tone="반말",
                recent_topic="사냥",
                last_message="사냥터는 여기 괜찮아.",
            )
        ],
    )
    response = robot_learning_digest_service.apply_digest(request)
    learning = store.get_learning_state("robot_2")
    issue_types = {issue["issue_type"] for issue in response.issues}
    assert response.issue_count == 2
    assert response.delete_talk_keys == [{"robot_uid": 2, "target_name": "유저", "target_kind": "pc"}]
    assert "item_supply_fallback" in issue_types
    assert "empty_talk" in issue_types
    assert learning["preferred_talk_topic"] == "사냥"


def test_survival_digest_updates_runtime_bias_for_next_decision() -> None:
    request = RobotLearningDigestRequest(
        server_name="test",
        tick=3,
        records=[
            RobotActionRecord(
                uid=201,
                agent_id="robot_survival_bias",
                robot_uid=201,
                action_type="dead",
                detail="로봇 사망",
                loc_x=100,
                loc_y=200,
                loc_map=4,
            )
        ],
    )
    response = robot_learning_digest_service.apply_digest(request)
    bias = store.get_learning_state("autogrowth::robot_survival_bias")["runtime_bias"]
    state = AgentState(
        hp=38,
        mp=20,
        x=100,
        y=200,
        map_id=4,
        target_id="mob_1",
        target_distance=2,
        is_under_attack=True,
        can_teleport=True,
        must_use_hp_item=False,
        inventory={},
    )
    decision = policy_engine.decide(state, runtime_override={"runtime_bias": bias})
    assert response.issue_count == 1
    assert bias["risk_mode"] == "safe"
    assert decision.action == "RETREAT"


def test_learning_digest_detects_runtime_and_talk_memory_issues() -> None:
    request = RobotLearningDigestRequest(
        server_name="test",
        tick=4,
        records=[
            RobotActionRecord(
                uid=301,
                agent_id="robot_runtime",
                robot_uid=301,
                action_type="runtime_exception",
                detail="phase=timer,error=java.lang.NullPointerException",
            ),
            RobotActionRecord(
                uid=302,
                agent_id="robot_runtime",
                robot_uid=301,
                action_type="aia_decide",
                detail="action=MOVE|confidence=0.20|source=rule_engine|reason=low",
            ),
        ],
        talk_memories=[
            RobotTalkMemoryRecord(
                robot_uid=301,
                agent_id="robot_runtime",
                target_name="유저",
                recent_topic="인사",
                last_message="",
            )
        ],
    )
    response = robot_learning_digest_service.apply_digest(request)
    issue_types = {issue["issue_type"] for issue in response.issues}
    assert "runtime_exception" in issue_types
    assert "low_confidence_decision" in issue_types
    assert "empty_talk_memory" in issue_types
    assert response.delete_talk_keys == []


def test_learning_digest_treats_single_collision_relief_as_benign() -> None:
    request = RobotLearningDigestRequest(
        server_name="test",
        tick=5,
        records=[
            RobotActionRecord(
                uid=401,
                agent_id="robot_collision",
                robot_uid=401,
                action_type="collision_relief",
                detail="이동 경로 막힘 우회",
                loc_x=32429,
                loc_y=32979,
                loc_map=0,
            )
        ],
    )
    response = robot_learning_digest_service.apply_digest(request)
    issue_types = {issue["issue_type"] for issue in response.issues}
    assert response.issue_count == 0
    assert "movement_stall" not in issue_types
