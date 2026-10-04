from datetime import date, datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.pagination import ListParams
from app.modules.projects.models import ProjectStatus
from app.modules.users.schemas import Name, UserOption


class ProjectWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Name
    description: str = Field(default="", max_length=20000)
    goal: str = Field(default="", max_length=20000)
    start_date: date | None = None
    deadline: date | None = None
    status: ProjectStatus = ProjectStatus.PLANNED
    responsible_user_id: UUID
    participant_ids: list[UUID] = Field(default_factory=list, max_length=500)

    @model_validator(mode="after")
    def valid_dates(self) -> Self:
        if self.start_date and self.deadline and self.deadline < self.start_date:
            raise ValueError("Deadline cannot be before start date")
        return self


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: str
    goal: str
    start_date: date | None
    deadline: date | None
    status: ProjectStatus
    responsible_user_id: UUID
    responsible_name: str
    participants: list[UserOption]
    created_at: datetime
    updated_at: datetime


class ProjectOption(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str


class ProjectFilters(ListParams):
    status: ProjectStatus | None = None
    responsible_user_id: UUID | None = None
    sort: Literal["name", "status", "updated_at", "created_at"] = "updated_at"
    direction: Literal["asc", "desc"] = "desc"
