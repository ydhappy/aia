from pydantic import BaseModel, Field


class AdminRobotSummaryResponse(BaseModel):
    agent_id: str
    has_state: bool = False
    has_profile: bool = False
    has_trace: bool = False
    has_learning: bool = False
    active_tasks: int = 0


class AdminSystemSummaryResponse(BaseModel):
    robots: list[AdminRobotSummaryResponse] = Field(default_factory=list)


class RecoveryActionResponse(BaseModel):
    agent_id: str
    action: str
    message: str
