from fastapi import APIRouter

from app.models.response_models import MetricsResponse
from app.services.store_factory import store


router = APIRouter(tags=["metrics"])


@router.get("/metrics", response_model=MetricsResponse)
def metrics() -> MetricsResponse:
    data = store.metrics()
    return MetricsResponse(**data)
