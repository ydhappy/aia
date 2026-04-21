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
