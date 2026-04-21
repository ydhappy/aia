from app.models.request_models import AgentState
from app.services.policy_engine import policy_engine


def make_state(**kwargs):
    base = dict(
        hp=90,
        mp=20,
        x=0,
        y=0,
        map_id=1,
        heading=0,
        target_id=None,
        target_distance=None,
        target_hp=None,
        is_under_attack=False,
        nearby_enemies=0,
        nearby_allies=0,
        safe_zone=False,
        can_teleport=False,
        weight_percent=20,
        cooldowns={},
        inventory={},
        buffs=[],
        debuffs=[],
        aggro_targets=[],
        extras={},
    )
    base.update(kwargs)
    return AgentState(**base)


def test_collector_picks_up_on_loot_event() -> None:
    state = make_state()
    profile = {"role": "collector", "style": "balanced"}
    events = [{"event_type": "loot_detected", "severity": "low"}]
    result = policy_engine.decide(state, profile=profile, recent_events=events)
    assert result.action == "PICKUP"


def test_high_severity_event_forces_retreat() -> None:
    state = make_state(is_under_attack=True, nearby_enemies=3, can_teleport=True)
    events = [{"event_type": "danger_zone", "severity": "high"}]
    result = policy_engine.decide(state, profile={}, recent_events=events)
    assert result.action == "RETREAT"


def test_tank_uses_control_skill_when_surrounded() -> None:
    state = make_state(target_id="mob_1", target_distance=1, nearby_enemies=3)
    profile = {"role": "tank", "style": "defensive", "banned_skills": []}
    result = policy_engine.decide(state, profile=profile, recent_events=[])
    assert result.action == "USE_SKILL"
