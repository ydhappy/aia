from fastapi import APIRouter

from app.core.config import settings
from app.core.mysql import connect_mysql
from app.models.response_models import HealthResponse
from app.services.llm_client import llm_client


SPAWN_QUEUE_TABLE = "aia_robot_spawn_request"
DB_BRIDGE_TABLES = [
    "aia_robot_state",
    "aia_robot_event",
    "aia_robot_feedback",
    "aia_robot_decision",
    "aia_robot_trace_summary",
]

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
    return {
        "app": settings.app_name,
        "status": "ok",
        "llm_backend": settings.llm_backend,
        "llm_status": llm_client.health(),
        "state_store": settings.state_store_mode,
        "db_bridge_backend": settings.db_bridge_backend,
        "mysql": _mysql_health(),
    }


def _mysql_health() -> dict:
    if settings.db_bridge_backend.lower() != "mysql":
        return {
            "enabled": False,
            "status": "skipped",
            "reason": "db_bridge_backend_not_mysql",
            "tables": {},
        }
    try:
        with connect_mysql(settings.db_bridge_mysql_dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 AS ok")
                row = cur.fetchone() or {}
                tables = _mysql_table_status(cur)
        missing_tables = [name for name, info in tables.items() if not info.get("exists")]
        return {
            "enabled": True,
            "status": "ok" if int(row.get("ok", 0)) == 1 else "unknown",
            "missing_tables": missing_tables,
            "tables": tables,
        }
    except Exception as exc:
        return {
            "enabled": True,
            "status": "error",
            "reason": str(exc),
            "missing_tables": [SPAWN_QUEUE_TABLE] + DB_BRIDGE_TABLES,
            "tables": _fallback_table_status(False),
        }


def _mysql_table_status(cur) -> dict:
    tables: dict[str, dict] = {}
    for table_name, required_sql in _required_tables().items():
        cur.execute("SHOW TABLES LIKE %s", (table_name,))
        tables[table_name] = {
            "exists": cur.fetchone() is not None,
            "required_sql": required_sql,
        }
    return tables


def _fallback_table_status(exists: bool) -> dict:
    return {
        table_name: {
            "exists": exists,
            "required_sql": required_sql,
        }
        for table_name, required_sql in _required_tables().items()
    }


def _required_tables() -> dict[str, str]:
    result = {SPAWN_QUEUE_TABLE: "sql/aia_robot_spawn_request_mysql55.sql"}
    for table_name in DB_BRIDGE_TABLES:
        result[table_name] = "sql/aia_robot_schema.sql"
    return result
