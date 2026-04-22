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


def test_must_use_hp_item_prefers_infinite_heal() -> None:
    state = AgentState(
        hp=94,
        mp=20,
        x=0,
        y=0,
        target_id="mob_1",
        target_distance=2,
        is_under_attack=False,
        must_use_hp_item=True,
        inventory={"infinite_healing_potion": 1, "potion": 1},
    )
    result = policy_engine.decide(state)
    assert result.action == "USE_SKILL"
    assert result.action_args["item"] == "infinite_healing_potion"
    assert result.reason == "hp_below_95_use_infinite_healing"


def test_safe_zone_runtime_kite_is_normalized_to_patrol() -> None:
    state = AgentState(
        hp=90,
        mp=20,
        x=32700,
        y=32800,
        map_id=4,
        safe_zone=True,
        target_id="mob_1",
        target_distance=4,
        is_under_attack=False,
        inventory={},
    )
    result = policy_engine.decide(
        state,
        runtime_override={"runtime_bias": {"move_mode": "kite"}},
    )
    assert result.action == "MOVE"
    assert result.action_args["mode"] == "patrol"


def test_safe_zone_forced_move_kite_is_normalized_to_patrol() -> None:
    state = AgentState(
        hp=90,
        mp=20,
        x=32700,
        y=32800,
        map_id=4,
        safe_zone=True,
        inventory={},
    )
    result = policy_engine.decide(
        state,
        runtime_override={"override": {"forced_action": "MOVE", "forced_mode": "kite"}},
    )
    assert result.action == "MOVE"
    assert result.action_args["mode"] == "patrol"
