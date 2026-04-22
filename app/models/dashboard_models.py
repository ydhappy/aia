from typing import Any

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


class RobotAiChecklistItem(BaseModel):
    key: str
    title: str
    status: str = "unknown"
    severity: str = "low"
    detail: str = ""
    action: str = ""


class RobotAiOpsDashboardResponse(BaseModel):
    system_name: str = "AIA Robot Autonomy Core"
    dependency_score: int = Field(default=0, ge=0, le=120)
    mode: str = "aia_first_server_minimal"
    total_agents: int = 0
    active_agents: int = 0
    learning_agents: int = 0
    issue_count: int = 0
    checklist: list[RobotAiChecklistItem] = Field(default_factory=list)
    navigation_algorithms: list[str] = Field(default_factory=list)
    runtime_layers: list[str] = Field(default_factory=list)
    server_minimal_contract: dict[str, Any] = Field(default_factory=dict)
    navigation_contract: dict[str, Any] = Field(default_factory=dict)
    quality_gates: list[dict[str, Any]] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    learning_summary: dict[str, Any] = Field(default_factory=dict)
    autonomy_baseline: dict[str, Any] = Field(default_factory=dict)
    cleanup_policy: dict[str, Any] = Field(default_factory=dict)
