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
    must_use_hp_item: bool = False
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


RobotRole = Literal[
    "tank",
    "healer",
    "dealer",
    "collector",
    "support",
    "scout",
    "siege_offense",
    "siege_defense",
    "custom",
]
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


class RobotProfilePatchRequest(BaseModel):
    name: str | None = None
    role: RobotRole | None = None
    style: RobotStyle | None = None
    party_id: str | None = None
    clan_id: str | None = None
    home_x: int | None = None
    home_y: int | None = None
    patrol_points: list[dict[str, int]] | None = None
    preferred_skills: list[str] | None = None
    banned_skills: list[str] | None = None
    tags: list[str] | None = None
    notes: list[str] | None = None
    metadata: dict[str, Any] | None = None


class RobotSpawnRequestCreateRequest(BaseModel):
    server_name: str = "main"
    count: int = Field(default=30, ge=1, le=500)
    request_prefix: str = "aia-api"
    agent_prefix: str = "aia_robot"
    name_prefix: str = "AIA로봇"
    classes: list[str] = Field(default_factory=lambda: ["knight", "elf", "wizard"])
    level_min: int = Field(default=1, ge=1)
    level_max: int = Field(default=30, ge=1)
    priority: int = Field(default=100, ge=0, le=10000)
    default_x: int = 32670
    default_y: int = 32790
    default_map: int = 4
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


class RobotActionRecord(BaseModel):
    uid: int = Field(ge=0)
    agent_id: str
    robot_uid: int | None = Field(default=None, ge=0)
    object_id: int | None = Field(default=None, ge=0)
    name: str | None = None
    action_type: str
    detail: str | None = None
    loc_x: int = 0
    loc_y: int = 0
    loc_map: int = 0
    created_at: int = Field(default=0, ge=0)


class RobotTalkMemoryRecord(BaseModel):
    robot_uid: int = Field(ge=0)
    agent_id: str
    target_name: str | None = None
    target_kind: Literal["pc", "robot"] = "pc"
    familiarity: int = Field(default=0, ge=0, le=100)
    conversation_count: int = Field(default=0, ge=0)
    tone: str | None = None
    recent_topic: str | None = None
    last_message: str | None = None
    updated_at: int = Field(default=0, ge=0)


class RobotLearningDigestRequest(BaseModel):
    server_name: str = "unknown"
    tick: int = Field(default=0, ge=0)
    reason: str = "periodic"
    records: list[RobotActionRecord] = Field(default_factory=list)
    talk_memories: list[RobotTalkMemoryRecord] = Field(default_factory=list)
    delete_after_apply: bool = True
