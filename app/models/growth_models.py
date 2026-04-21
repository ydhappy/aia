from pydantic import BaseModel, Field


class GrowthStateResponse(BaseModel):
    agent_id: str
    stage: str = "novice"
    scores: dict[str, float] = Field(default_factory=dict)
    mastery: dict[str, float] = Field(default_factory=dict)
    failure_tags: list[str] = Field(default_factory=list)
