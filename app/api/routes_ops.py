from fastapi import APIRouter, Depends

from app.core.security import verify_api_key
from app.services.memory_summary_service import memory_summary_service
from app.services.scheduler_service import scheduler_service


router = APIRouter(prefix="/ops", tags=["ops"], dependencies=[Depends(verify_api_key)])


@router.post("/scheduler/run")
def run_scheduler(agent_ids: list[str]) -> dict:
    return scheduler_service.run_cycle(agent_ids)


@router.get("/memory/{agent_id}")
def memory_summary(agent_id: str) -> dict:
    return memory_summary_service.summarize_agent(agent_id)
