from datetime import datetime
from typing import Annotated, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

CommentText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20000)
]


class CommentOwner(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: UUID | None = None
    task_id: UUID | None = None
    setup_id: UUID | None = None
    test_id: UUID | None = None
    branch_id: UUID | None = None

    @model_validator(mode="after")
    def exactly_one_owner(self) -> Self:
        if (
            sum(
                value is not None
                for value in (
                    self.project_id,
                    self.task_id,
                    self.setup_id,
                    self.test_id,
                    self.branch_id,
                )
            )
            != 1
        ):
            raise ValueError("Вкажіть рівно один запис, до якого належить коментар.")
        return self


class CommentCreate(CommentOwner):
    text: CommentText


class CommentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: CommentText


class CommentRead(CommentOwner):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    author_id: UUID
    author_name: str
    text: str
    created_at: datetime
    updated_at: datetime


class CommentFilters(CommentOwner):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
