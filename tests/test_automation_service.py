from app.models.auto import AutomationTaskRequest
from app.services.automation_service import automation_service


def test_create_and_list_automation_task() -> None:
    req = AutomationTaskRequest(
        agent_id="bot_auto_1",
        mode="farm",
        priority=80,
        conditions={"hp_below": 30},
        parameters={"area": "field_a"},
    )
    res = automation_service.create_task(req)
    tasks = automation_service.list_tasks("bot_auto_1")
    assert res.agent_id == "bot_auto_1"
    assert len(tasks.tasks) >= 1


def test_next_step_returns_mode_specific_objective() -> None:
    req = AutomationTaskRequest(
        agent_id="bot_auto_2",
        mode="patrol",
        priority=70,
        parameters={"points": [{"x": 1, "y": 2}]},
    )
    automation_service.create_task(req)
    decision = automation_service.decide_next_step("bot_auto_2", {})
    assert decision.next_step["mode"] == "patrol"
