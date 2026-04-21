from fastapi import APIRouter, Depends

from app.core.security import verify_api_key
from app.services.automation_service import automation_service
from app.services.economy_service import economy_service
from app.services.goal_service import goal_service
from app.services.growth_service import growth_service
from app.services.npc_service import npc_service
from app.services.state_machine_service import state_machine_service
from app.services.store_factory import store
from app.services.talk_service import talk_service


router = APIRouter(prefix="/goal", tags=["goal"], dependencies=[Depends(verify_api_key)])


@router.get("/{agent_id}")
def goal_state(agent_id: str) -> dict:
    goal = goal_service.build_goal_state(agent_id).model_dump()
    fsm = state_machine_service.next_state(agent_id)
    economy = economy_service.next_economy_step(agent_id)
    npc = npc_service.next_npc_step(agent_id)
    state_wrapper = store.get_state(agent_id) or {}
    state = state_wrapper.get("state", {}) if isinstance(state_wrapper, dict) else {}
    next_step = automation_service.decide_next_step(agent_id, state).next_step
    growth = growth_service.get_growth_state(agent_id).model_dump()
    trace = store.get_trace(agent_id) or {}
    anomalies = trace.get("anomalies", {"detected": False, "anomalies": []}) if isinstance(trace, dict) else {"detected": False, "anomalies": []}
    talk = talk_service.build_talk(goal, growth, anomalies, next_step)
    return {
        "goal": goal,
        "state_machine": fsm,
        "economy": economy,
        "npc": npc,
        "next_step": next_step,
        "growth": growth,
        "talk": talk,
    }
