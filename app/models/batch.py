from pydantic import BaseModel, Field

from app.models.req import DecideRequest, ObserveRequest
from app.models.res import DecideResponse, ObserveResponse


class BatchObserveRequest(BaseModel):
    items: list[ObserveRequest] = Field(default_factory=list)


class BatchObserveResponse(BaseModel):
    items: list[ObserveResponse] = Field(default_factory=list)


class BatchDecideRequest(BaseModel):
    items: list[DecideRequest] = Field(default_factory=list)


class BatchDecideResponse(BaseModel):
    items: list[DecideResponse] = Field(default_factory=list)
