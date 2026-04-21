from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes_admin import router as admin_router
from app.api.routes_agent import router as agent_router
from app.api.routes_automation import router as automation_router
from app.api.routes_batch import router as batch_router
from app.api.routes_dashboard import router as dashboard_router
from app.api.routes_db_bridge import router as db_bridge_router
from app.api.routes_goal import router as goal_router
from app.api.routes_health import router as health_router
from app.api.routes_knowledge import router as knowledge_router
from app.api.routes_metrics import router as metrics_router
from app.api.routes_ops import router as ops_router
from app.api.routes_scale import router as scale_router
from app.api.routes_unified import router as unified_router
from app.api.routes_ws import router as ws_router
from app.core.config import settings
from app.core.security import ApiKeyError


app = FastAPI(
    title=settings.app_name,
    version="0.12.0",
    description="Lightweight AI bridge server for game server integration.",
)


@app.exception_handler(ApiKeyError)
async def api_key_error_handler(request: Request, exc: ApiKeyError) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": str(exc)})


app.include_router(health_router)
app.include_router(agent_router)
app.include_router(admin_router)
app.include_router(automation_router)
app.include_router(batch_router)
app.include_router(dashboard_router)
app.include_router(db_bridge_router)
app.include_router(goal_router)
app.include_router(metrics_router)
app.include_router(knowledge_router)
app.include_router(ops_router)
app.include_router(scale_router)
app.include_router(unified_router)
app.include_router(ws_router)


@app.get("/")
def root() -> dict:
    return {
        "name": settings.app_name,
        "status": "ok",
        "message": "AIA is running.",
    }
