from fastapi import FastAPI

from app.api.routes_agent import router as agent_router
from app.api.routes_health import router as health_router
from app.api.routes_knowledge import router as knowledge_router
from app.api.routes_metrics import router as metrics_router
from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="Lightweight AI bridge server for game server integration.",
)

app.include_router(health_router)
app.include_router(agent_router)
app.include_router(metrics_router)
app.include_router(knowledge_router)


@app.get("/")
def root() -> dict:
    return {
        "name": settings.app_name,
        "status": "ok",
        "message": "AIA is running.",
    }
