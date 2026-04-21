from fastapi import APIRouter, Depends

from app.core.security import verify_api_key
from app.services.economy_service import economy_service
from app.services.goal_service import goal_service
from app.services.npc_service import npc_service
from app.services.state_machine_service import state_machine_service


router = APIRouter(prefix="/goal", tags=["goal"], dependencies=[Depends(verify_api_key)])


@router.get("/{agent_id}")
def goal_state(agent_id: str) -> dict:
    return {
        "goal": goal_service.build_goal_state(agent_id).model_dump(),
        "state_machine": state_machine_service.next_state(agent_id),
        "economy": economy_service.next_economy_step(agent_id),
        "npc": npc_service.next_npc_step(agent_id),
    }
