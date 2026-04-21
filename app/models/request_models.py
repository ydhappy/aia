from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentState(BaseModel):
    hp: int = Field(ge=0)
    mp: int = Field(ge=0)
    x: int
    y: int
    target_id: str | None = None
    target_distance: int | None = Field(default=None, ge=0)
    is_under_attack: bool = False
    cooldowns: dict[str, int] = Field(default_factory=dict)
    inventory: dict[str, int] = Field(default_factory=dict)
    extras: dict[str, Any] = Field(default_factory=dict)


class ObserveRequest(BaseModel):
    agent_id: str
    tick: int = Field(ge=0)
    state: AgentState


class DecideRequest(BaseModel):
    agent_id: str
    tick: int = Field(ge=0)
    state: AgentState


RobotRole = Literal["tank", "healer", "dealer", "collector", "support", "scout", "custom"]
RobotStyle = Literal["aggressive", "defensive", "balanced", "support", "custom"]


class RobotProfileRequest(BaseModel):
    agent_id: str
    name: str | None = None
    role: RobotRole = "custom"
    style: RobotStyle = "balanced"
    party_id: str | None = None
    home_x: int | None = None
    home_y: int | None = None
    preferred_skills: list[str] = Field(default_factory=list)
    banned_skills: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RobotEventRequest(BaseModel):
    agent_id: str
    tick: int = Field(ge=0)
    event_type: str
    severity: Literal["low", "medium", "high"] = "low"
    message: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
