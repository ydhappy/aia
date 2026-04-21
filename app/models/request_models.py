from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentState(BaseModel):
    hp: int = Field(ge=0)
    mp: int = Field(ge=0)
    x: int
    y: int
    map_id: int | None = None
    heading: int | None = None
    target_id: str | None = None
    target_distance: int | None = Field(default=None, ge=0)
    target_hp: int | None = Field(default=None, ge=0)
    is_under_attack: bool = False
    nearby_enemies: int = Field(default=0, ge=0)
    nearby_allies: int = Field(default=0, ge=0)
    safe_zone: bool = False
    can_teleport: bool = False
    weight_percent: int | None = Field(default=None, ge=0, le=100)
    cooldowns: dict[str, int] = Field(default_factory=dict)
    inventory: dict[str, int] = Field(default_factory=dict)
    buffs: list[str] = Field(default_factory=list)
    debuffs: list[str] = Field(default_factory=list)
    aggro_targets: list[str] = Field(default_factory=list)
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
    clan_id: str | None = None
    home_x: int | None = None
    home_y: int | None = None
    patrol_points: list[dict[str, int]] = Field(default_factory=list)
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


class RobotFeedbackRequest(BaseModel):
    agent_id: str
    tick: int = Field(ge=0)
    action: str
    reward: float = 0.0
    outcome: Literal["success", "partial", "failure"] = "partial"
    context: dict[str, Any] = Field(default_factory=dict)
