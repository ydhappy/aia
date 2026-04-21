from fastapi import APIRouter, Depends

from app.core.security import verify_api_key
from app.services.alert_service import alert_service
from app.services.dashboard_service import dashboard_service


router = APIRouter(prefix="/alerts", tags=["alerts"], dependencies=[Depends(verify_api_key)])


@router.post("/evaluate")
def evaluate_alerts(agent_ids: list[str]) -> dict:
    summary = dashboard_service.counts(agent_ids).model_dump()
    alert_result = alert_service.evaluate(summary)
    return {
        "summary": summary,
        "alerts": alert_result,
    }
