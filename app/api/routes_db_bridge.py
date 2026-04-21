from fastapi import APIRouter, Depends

from app.core.security import verify_api_key
from app.services.db_bridge_service import db_bridge_service


router = APIRouter(prefix="/db-bridge", tags=["db-bridge"], dependencies=[Depends(verify_api_key)])


@router.get("/states")
def poll_states() -> dict:
    return {"rows": db_bridge_service.poll_states()}


@router.get("/events")
def poll_events() -> dict:
    return {"rows": db_bridge_service.poll_events()}


@router.get("/feedback")
def poll_feedback() -> dict:
    return {"rows": db_bridge_service.poll_feedback()}


@router.post("/decision")
def write_decision(row: dict) -> dict:
    return db_bridge_service.write_decision(row)


@router.post("/trace")
def write_trace_summary(row: dict) -> dict:
    return db_bridge_service.write_trace_summary(row)
