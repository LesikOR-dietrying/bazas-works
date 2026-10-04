from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.technology.models import ContentBlockType


class CardWrite(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=20000)


class CardRead(CardWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    revision_id: UUID
    created_at: datetime
    updated_at: datetime


class OperationWrite(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    sequence: int = Field(ge=0)
    expected_result: str = Field(default="", max_length=20000)
    acceptance_criteria: str = Field(default="", max_length=20000)


class OperationRead(OperationWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    card_id: UUID
    created_at: datetime
    updated_at: datetime


class BlockWrite(BaseModel):
    block_type: ContentBlockType
    sequence: int = Field(ge=0)
    payload: dict[str, object] = Field(default_factory=dict)
    attachment_id: UUID | None = None
    annotation_source: dict[str, object] = Field(default_factory=dict)
    annotation_version: int = Field(default=1, ge=1)


class BlockRead(BlockWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    operation_id: UUID
    created_at: datetime
    updated_at: datetime


class ChecklistWrite(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    sequence: int = Field(ge=0)
    required: bool = True
    note_required: bool = False
    photo_required: bool = False


class ChecklistRead(ChecklistWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    block_id: UUID
    created_at: datetime
    updated_at: datetime


class OperationPreview(OperationRead):
    blocks: list[BlockRead]
    checklist_items: list[ChecklistRead]


class WorkerPreview(BaseModel):
    card: CardRead
    operations: list[OperationPreview]
