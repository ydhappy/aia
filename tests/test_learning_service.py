from app.models.request_models import RobotFeedbackRequest
from app.services.learning_service import learning_service


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
