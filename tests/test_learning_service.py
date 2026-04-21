from app.models.request_models import RobotFeedbackRequest
from app.services.learning_service import learning_service
from app.services.store_factory import store


def test_learning_feedback_updates_state() -> None:
    req = RobotFeedbackRequest(
        agent_id="bot_test_learning",
        tick=1,
        action="ATTACK",
        reward=1.0,
        outcome="success",
        context={},
    )
    learning_service.submit_feedback(req)
    state = learning_service.get_learning_state("bot_test_learning")
    assert state.learning_state["preferred_action"] == "ATTACK"


def test_learning_feedback_negative_action_marks_avoid() -> None:
    req = RobotFeedbackRequest(
        agent_id="bot_test_learning2",
        tick=1,
        action="RETREAT",
        reward=-1.0,
        outcome="failure",
        context={},
    )
    learning_service.submit_feedback(req)
    state = learning_service.get_learning_state("bot_test_learning2")
    assert state.learning_state["avoid_action"] == "RETREAT"


def test_learning_feedback_tracks_map_preferences() -> None:
    req = RobotFeedbackRequest(
        agent_id="bot_test_learning3",
        tick=1,
        action="MOVE",
        reward=2.0,
        outcome="success",
        context={"map_id": 99},
    )
    learning_service.submit_feedback(req)
    state = learning_service.get_learning_state("bot_test_learning3")
    assert state.learning_state["preferred_action_by_map"]["99"] == "MOVE"


def test_learning_feedback_updates_group_learning() -> None:
    req = RobotFeedbackRequest(
        agent_id="bot_test_learning4",
        tick=1,
        action="USE_SKILL",
        reward=1.5,
        outcome="success",
        context={"group_key": "raid_alpha"},
    )
    learning_service.submit_feedback(req)
    group_state = store.get_learning_state("group::raid_alpha")
    assert group_state["preferred_action"] == "USE_SKILL"
