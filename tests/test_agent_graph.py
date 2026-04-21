from app.graphs.agent_graph import agent_graph
from app.models.request_models import AgentState


def make_state(**kwargs):
    data = dict(
        hp=40,
        mp=20,
        x=0,
        y=0,
        map_id=1,
        heading=0,
        target_id=None,
        target_distance=None,
        target_hp=None,
        is_under_attack=True,
        nearby_enemies=2,
        nearby_allies=1,
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
    data.update(kwargs)
    return AgentState(**data)


def test_agent_graph_builds_trace() -> None:
    state = make_state()
    trace = agent_graph.run("bot_1", state, {"role": "healer", "style": "support"}, [])
    assert trace["agent_id"] == "bot_1"
    assert "risk_score" in trace
    assert "strategy" in trace
    assert "profile_hint" in trace


def test_agent_graph_requests_llm_when_profile_has_notes() -> None:
    state = make_state()
    trace = agent_graph.run("bot_1", state, {"notes": ["be careful"]}, [])
    assert trace["llm_hint"] is True
