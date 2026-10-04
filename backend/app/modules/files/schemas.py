from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OwnerReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: UUID | None = None
    task_id: UUID | None = None
    setup_id: UUID | None = None
    component_id: UUID | None = None
    test_id: UUID | None = None
    firmware_revision_id: UUID | None = None
    branch_id: UUID | None = None
    product_id: UUID | None = None
    product_revision_id: UUID | None = None
    firmware_release_id: UUID | None = None
    stage_execution_id: UUID | None = None

    @model_validator(mode="after")
    def exactly_one_owner(self) -> Self:
        owners = (
            self.project_id,
            self.task_id,
            self.setup_id,
            self.component_id,
            self.test_id,
            self.firmware_revision_id,
            self.branch_id,
            self.product_id,
            self.product_revision_id,
            self.firmware_release_id,
            self.stage_execution_id,
        )
        if sum(value is not None for value in owners) != 1:
            raise ValueError("Вкажіть рівно один запис, до якого належить файл.")
        return self


class AttachmentRead(OwnerReference):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str
    mime_type: str
    size: int
    uploaded_by_id: UUID
    uploaded_by_name: str
    created_at: datetime


class AttachmentFilters(OwnerReference):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
