from fastapi import APIRouter

from app.core.config import settings
from app.core.mysql import connect_mysql
from app.models.response_models import HealthResponse
from app.services.llm_client import llm_client


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        app=settings.app_name,
        status="ok",
        llm_backend=settings.llm_backend,
        llm_status=llm_client.health(),
        state_store=settings.state_store_mode,
    )


@router.get("/health/details")
def health_details() -> dict:
    details = {
        "app": settings.app_name,
        "status": "ok",
        "llm_backend": settings.llm_backend,
        "llm_status": llm_client.health(),
        "state_store": settings.state_store_mode,
        "db_bridge_backend": settings.db_bridge_backend,
        "mysql": _mysql_health(),
    }
    return details


def _mysql_health() -> dict:
    if settings.db_bridge_backend.lower() != "mysql":
        return {
            "enabled": False,
            "status": "skipped",
            "reason": "db_bridge_backend_not_mysql",
        }
    try:
        with connect_mysql(settings.db_bridge_mysql_dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 AS ok")
                row = cur.fetchone() or {}
        return {
            "enabled": True,
            "status": "ok" if int(row.get("ok", 0)) == 1 else "unknown",
        }
    except Exception as exc:
        return {
            "enabled": True,
            "status": "error",
            "reason": str(exc),
        }
