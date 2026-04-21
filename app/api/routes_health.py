from fastapi import APIRouter

from app.core.config import settings
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
