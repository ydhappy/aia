from pydantic import BaseModel, Field

from app.models.automation_models import AutomationTaskRequest
from app.models.request_models import (
    ObserveRequest,
    RobotEventRequest,
    RobotFeedbackRequest,
    RobotProfileRequest,
)
from app.models.response_models import (
    ObserveResponse,
    RobotEventResponse,
    RobotFeedbackResponse,
    RobotProfileResponse,
)


class UnifiedRobotSyncRequest(BaseModel):
    profile: RobotProfileRequest | None = None
    events: list[RobotEventRequest] = Field(default_factory=list)
    observe: ObserveRequest | None = None
    feedback: RobotFeedbackRequest | None = None
    automation_task: AutomationTaskRequest | None = None


class UnifiedRobotSyncResponse(BaseModel):
    profile_result: RobotProfileResponse | None = None
    event_results: list[RobotEventResponse] = Field(default_factory=list)
    observe_result: ObserveResponse | None = None
    feedback_result: RobotFeedbackResponse | None = None
    automation_result: dict = Field(default_factory=dict)
