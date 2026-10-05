from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RouteWrite(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    version: int = Field(default=1, ge=1)
    description: str = Field(default="", max_length=20000)


class RouteRead(RouteWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    revision_id: UUID
    created_at: datetime
    updated_at: datetime


class StageWrite(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    sequence: int = Field(ge=0)
    technology_operation_id: UUID | None = None
    supports_pass_fail: bool = True
    measurement_required: bool = False
    attachment_required: bool = False
    instructions: str = Field(default="", max_length=20000)
    role_ids: list[UUID] = Field(default_factory=list)


class RouteRoleRead(BaseModel):
    id: UUID
    code: str
    name: str


class StageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    route_id: UUID
    code: str
    name: str
    sequence: int
    technology_operation_id: UUID | None
    supports_pass_fail: bool
    measurement_required: bool
    attachment_required: bool
    instructions: str
    roles: list[RouteRoleRead] = Field(default_factory=list)
    predecessor_ids: list[UUID] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class DependencyWrite(BaseModel):
    predecessor_id: UUID


class DependencyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    stage_id: UUID
    predecessor_id: UUID
