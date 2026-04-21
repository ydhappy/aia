from typing import Any

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
