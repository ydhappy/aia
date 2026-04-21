from typing import Any, Literal

from pydantic import BaseModel, Field


AutomationMode = Literal[
    "farm",
    "patrol",
    "escort",
    "support_loop",
    "loot_loop",
    "boss_watch",
    "return_and_resume",
    "custom",
]

TaskStatus = Literal["pending", "running", "paused", "completed", "failed"]


class RobotAutomationTask(BaseModel):
    task_id: str
    agent_id: str
    mode: AutomationMode
    status: TaskStatus = "pending"
    priority: int = Field(default=50, ge=0, le=100)
    conditions: dict[str, Any] = Field(default_factory=dict)
    parameters: dict[str, Any] = Field(default_factory=dict)


class AutomationTaskRequest(BaseModel):
    agent_id: str
    mode: AutomationMode
    priority: int = Field(default=50, ge=0, le=100)
    conditions: dict[str, Any] = Field(default_factory=dict)
    parameters: dict[str, Any] = Field(default_factory=dict)


class AutomationTaskResponse(BaseModel):
    accepted: bool = True
    agent_id: str
    task_id: str
    message: str = "automation task stored"


class AutomationTaskListResponse(BaseModel):
    agent_id: str
    tasks: list[RobotAutomationTask] = Field(default_factory=list)


class AutomationDecisionResponse(BaseModel):
    agent_id: str
    active_task: dict[str, Any] = Field(default_factory=dict)
    next_step: dict[str, Any] = Field(default_factory=dict)
