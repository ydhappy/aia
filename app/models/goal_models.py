from pydantic import BaseModel, Field


class GoalStateResponse(BaseModel):
    agent_id: str
    primary_goal: str = "idle"
    secondary_goals: list[str] = Field(default_factory=list)
    next_phase: str = "idle"
    notes: list[str] = Field(default_factory=list)
