from typing import Any, Literal

from pydantic import BaseModel, Field


AllowedAction = Literal["MOVE", "ATTACK", "USE_SKILL", "RETREAT", "PICKUP", "IDLE"]


class ObserveResponse(BaseModel):
    accepted: bool = True
    agent_id: str
    tick: int
    message: str = "state stored"


class DecideResponse(BaseModel):
    action: AllowedAction
    action_args: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    source: Literal["rule_engine", "llm", "fallback"] = "rule_engine"


class HealthResponse(BaseModel):
    app: str
    status: str
    llm_backend: str
    llm_status: str
    state_store: str


class MetricsResponse(BaseModel):
    total_observe_requests: int
    total_decide_requests: int
    total_fallbacks: int
    total_profiles_saved: int
    total_events_saved: int


class RobotProfileResponse(BaseModel):
    accepted: bool = True
    agent_id: str
    message: str = "robot profile stored"


class RobotEventResponse(BaseModel):
    accepted: bool = True
    agent_id: str
    message: str = "robot event stored"


class RobotKnowledgeResponse(BaseModel):
    agent_id: str
    profile: dict[str, Any] = Field(default_factory=dict)
    recent_events: list[dict[str, Any]] = Field(default_factory=list)
    last_state: dict[str, Any] | None = None


class AgentTraceResponse(BaseModel):
    agent_id: str
    trace: dict[str, Any] = Field(default_factory=dict)
