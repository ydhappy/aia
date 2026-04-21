from app.models.request_models import AgentState
from app.services.policy_engine import policy_engine


def test_retreat_on_critical_hp() -> None:
    state = AgentState(
        hp=10,
        mp=20,
        x=0,
        y=0,
        target_id="mob_1",
        target_distance=1,
        is_under_attack=True,
        cooldowns={"heal": 0},
        inventory={"potion": 1},
    )
    result = policy_engine.decide(state)
    assert result.action == "RETREAT"


def test_heal_when_low_hp_and_heal_ready() -> None:
    state = AgentState(
        hp=40,
        mp=20,
        x=0,
        y=0,
        target_id="mob_1",
        target_distance=1,
        is_under_attack=True,
        cooldowns={"heal": 0},
        inventory={"potion": 1},
    )
    result = policy_engine.decide(state)
    assert result.action == "USE_SKILL"


def test_attack_when_target_in_range() -> None:
    state = AgentState(
        hp=90,
        mp=20,
        x=0,
        y=0,
        target_id="mob_1",
        target_distance=1,
        is_under_attack=False,
        cooldowns={"heal": 5},
        inventory={},
    )
    result = policy_engine.decide(state)
    assert result.action == "ATTACK"
