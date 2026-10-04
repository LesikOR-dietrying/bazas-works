from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.pagination import ListParams
from app.modules.orders.models import OrderStatus
from app.modules.production.models import ExecutionStatus


class LaunchRead(BaseModel):
    order_id: UUID
    created_items: int


class ProductionItemRead(BaseModel):
    id: UUID
    identifier: str
    tracking_mode: str
    quantity: int
    variant_id: UUID
    variant_name: str
    product_name: str
    revision_code: str
    order_number: str
    qr_value: str


class ExecutionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    production_item_id: UUID
    stage_id: UUID
    stage_code: str
    stage_name: str
    attempt: int
    planned_quantity: int
    completed_quantity: int
    failed_quantity: int
    status: ExecutionStatus
    assigned_user_id: UUID | None
    started_by_id: UUID | None
    started_at: datetime | None
    completed_by_id: UUID | None
    completed_at: datetime | None
    result_note: str


class WorkItemRead(BaseModel):
    item: ProductionItemRead
    execution: ExecutionRead


class ChecklistInput(BaseModel):
    template_item_id: UUID
    checked: bool
    note: str = ""
    photo_attachment_id: UUID | None = None


class CompleteWrite(BaseModel):
    quantity: int | None = Field(default=None, gt=0)
    result_note: str = Field(default="", max_length=20000)
    idempotency_key: UUID
    checklist: list[ChecklistInput] = Field(default_factory=list)


class AssignmentWrite(BaseModel):
    assigned_user_id: UUID | None


class ChecklistTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    text: str
    required: bool
    note_required: bool
    photo_required: bool


class ContentBlockRead(BaseModel):
    id: UUID
    block_type: str
    sequence: int
    payload: dict[str, object]
    attachment_id: UUID | None


class ExecutionDetailRead(BaseModel):
    item: ProductionItemRead
    execution: ExecutionRead
    instructions: str
    operation_name: str | None
    expected_result: str
    acceptance_criteria: str
    blocks: list[ContentBlockRead]
    checklist: list[ChecklistTemplateRead]


class StageProgressRead(BaseModel):
    stage_code: str
    stage_name: str
    completed: int
    total: int


class OrderProgressRead(BaseModel):
    order_id: UUID
    completed: int
    total: int
    percent: int
    stages: list[StageProgressRead]


class ProductionQueueFilters(ListParams):
    status: Literal["PRODUCTION", "READY"] | None = None


class ProductionQueueRead(BaseModel):
    order_id: UUID
    order_number: str
    customer_name: str
    deadline: date | None
    status: OrderStatus
    completed_quantity: int
    planned_quantity: int
    percent: int
    active_operations: int
    blocked_operations: int
    assignees: list[str]
    current_item_id: UUID | None
    current_item_identifier: str | None
    stages: list[StageProgressRead]
