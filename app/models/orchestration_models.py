from pydantic import BaseModel, Field


class FleetSyncRequest(BaseModel):
    agent_ids: list[str] = Field(default_factory=list)
    shard_key: str | None = None
    batch_size: int = Field(default=100, ge=1, le=1000)


class FleetSyncResponse(BaseModel):
    total_agents: int = 0
    shard_key: str | None = None
    batches: list[list[str]] = Field(default_factory=list)


class FleetSummaryResponse(BaseModel):
    total_agents: int = 0
    active_agents: int = 0
    robots_with_tasks: int = 0
    robots_with_learning: int = 0
    robots_with_trace: int = 0
