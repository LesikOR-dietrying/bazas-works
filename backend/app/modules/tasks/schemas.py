from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from app.core.pagination import ListParams
from app.modules.tasks.models import Priority, TaskStatus
from app.modules.users.schemas import Name


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Name
    description: str = Field(default="", max_length=20000)
    project_id: UUID
    branch_id: UUID | None = None
    assignee_id: UUID | None = None
    status: TaskStatus = TaskStatus.TODO
    priority: Priority = Priority.NORMAL
    deadline: AwareDatetime | None = None
    result: str = Field(default="", max_length=20000)


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Name | None = None
    description: str | None = Field(default=None, max_length=20000)
    project_id: UUID | None = None
    branch_id: UUID | None = None
    assignee_id: UUID | None = None
    status: TaskStatus | None = None
    priority: Priority | None = None
    deadline: AwareDatetime | None = None
    result: str | None = Field(default=None, max_length=20000)

    @model_validator(mode="after")
    def no_invalid_nulls(self) -> Self:
        if any(
            getattr(self, field) is None
            for field in self.model_fields_set - {"assignee_id", "deadline", "branch_id"}
        ):
            raise ValueError("Only assignee_id, deadline and branch_id can be null")
        if not self.model_fields_set:
            raise ValueError("Provide at least one field")
        return self


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    description: str
    project_id: UUID
    branch_id: UUID | None
    project_name: str
    assignee_id: UUID | None
    assignee_name: str | None
    created_by_id: UUID
    created_by_name: str
    status: TaskStatus
    priority: Priority
    deadline: datetime | None
    result: str
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TaskFilters(ListParams):
    assignee_id: UUID | None = None
    project_id: UUID | None = None
    branch_id: UUID | None = None
    status: TaskStatus | None = None
    priority: Priority | None = None
    mine: bool = False
    overdue: bool = False
    sort: Literal["title", "status", "priority", "deadline", "updated_at", "created_at"] = (
        "updated_at"
    )
    direction: Literal["asc", "desc"] = "desc"


class TaskSummary(BaseModel):
    total: int
    active: int
    overdue: int
    blocked: int
    completed: int
    completed_recently: int
