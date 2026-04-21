from pydantic import BaseModel, Field


class DashboardCountsResponse(BaseModel):
    total_agents: int = 0
    active_agents: int = 0
    agents_with_tasks: int = 0
    agents_with_learning: int = 0
    agents_with_trace: int = 0
    agents_needing_recovery: int = 0


class AgentFilterResult(BaseModel):
    agent_ids: list[str] = Field(default_factory=list)


class ShardAssignmentResponse(BaseModel):
    shard_key: str
    agent_ids: list[str] = Field(default_factory=list)
