from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.pagination import ListParams
from app.modules.orders.models import OrderStatus, VariantStatus


class CustomerWrite(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    contact_details: str = ""
    notes: str = ""


class CustomerRead(CustomerWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class OrderWrite(BaseModel):
    order_number: str = Field(min_length=1, max_length=100)
    customer_id: UUID
    recipient: str = ""
    destination: str = ""
    order_date: date
    deadline: date | None = None
    notes: str = ""


class OrderRead(OrderWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    status: OrderStatus
    draft_version: int
    customer_name: str
    total_quantity: int
    product_summary: str
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime


class OrderFilters(ListParams):
    status: OrderStatus | None = None
    customer_id: UUID | None = None


class OrderStatusWrite(BaseModel):
    status: OrderStatus
    expected_draft_version: int | None = Field(default=None, ge=1)


class ItemWrite(BaseModel):
    product_revision_id: UUID
    quantity: int = Field(gt=0)
    required_date: date | None = None
    notes: str = ""


class ItemRead(ItemWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    order_id: UUID
    product_id: UUID
    product_name: str
    revision_code: str
    created_at: datetime
    updated_at: datetime


class VariantWrite(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    quantity: int = Field(gt=0)
    notes: str = ""


class VariantRead(VariantWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    order_item_id: UUID
    is_standard: bool
    status: VariantStatus
    created_at: datetime
    updated_at: datetime


class DeviationWrite(BaseModel):
    original_bom_item_id: UUID
    replacement_component_id: UUID
    quantity_per_product: Decimal = Field(gt=0)
    reason: str = Field(min_length=1)
    notes: str = ""
    required_retest: bool = False
    test_ids: list[UUID] = Field(default_factory=list)


class DeviationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    variant_id: UUID
    original_bom_item_id: UUID
    replacement_component_id: UUID
    quantity_per_product: Decimal
    reason: str
    requested_by_id: UUID
    approved_by_id: UUID | None
    approved_at: datetime | None
    notes: str
    required_retest: bool
    created_at: datetime


class RequirementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    variant_id: UUID
    original_bom_item_id: UUID
    source_deviation_id: UUID | None
    component_id: UUID
    component_name: str
    uom_id: UUID
    required_quantity: Decimal


class MaterialSummary(BaseModel):
    component_id: UUID
    required: Decimal
    available: Decimal = Decimal(0)
    reserved: Decimal = Decimal(0)
    ordered: Decimal
    in_transit: Decimal
    missing: Decimal


class ReleasedRevisionOption(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    product_id: UUID
    product_name: str
    variant_id: UUID
    variant_name: str
    revision_code: str


class RequirementPreviewAlternative(BaseModel):
    component_id: UUID
    component_name: str
    component_sku: str | None
    notes: str


class RequirementPreviewRow(BaseModel):
    bom_item_id: UUID
    position: str
    component_id: UUID
    component_name: str
    component_sku: str | None
    quantity_per_product: Decimal
    total_quantity: Decimal
    uom_id: UUID
    uom_code: str
    alternatives: list[RequirementPreviewAlternative]
