from fastapi import APIRouter

from app.models.response_models import MetricsResponse
from app.services.state_store import state_store


router = APIRouter(tags=["metrics"])


@router.get("/metrics", response_model=MetricsResponse)
def metrics() -> MetricsResponse:
    data = state_store.metrics()
    return MetricsResponse(**data)
