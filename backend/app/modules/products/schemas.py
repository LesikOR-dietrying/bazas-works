from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.pagination import ListParams
from app.modules.products.models import ProductLifecycle, RevisionStatus, TrackingMode


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    code: str
    name: str
    description: str
    is_active: bool


class ProductWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    category_id: UUID
    description: str = Field(default="", max_length=20000)
    lifecycle: ProductLifecycle = ProductLifecycle.DEVELOPMENT
    tracking_mode: TrackingMode


class ProductRead(ProductWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    current_revision_id: UUID | None
    general_image_attachment_id: UUID | None
    category_name: str
    variant_count: int
    created_at: datetime
    updated_at: datetime


class ProductFilters(ListParams):
    category_id: UUID | None = None
    lifecycle: ProductLifecycle | None = None
    tracking_mode: TrackingMode | None = None


class RevisionWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision_code: str = Field(min_length=1, max_length=100)
    technical_characteristics: dict[str, object] = Field(default_factory=dict)
    standard_cost: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="UAH", min_length=3, max_length=3)
    revision_instructions: str = Field(default="", max_length=50000)


class VariantWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=20000)


class VariantRead(VariantWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    product_id: UUID
    is_active: bool
    current_revision_id: UUID | None
    created_at: datetime
    updated_at: datetime


class RevisionRead(RevisionWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    product_id: UUID
    variant_id: UUID
    variant_name: str
    product_name: str
    status: RevisionStatus
    source_project_id: UUID | None
    source_branch_id: UUID | None
    source_setup_id: UUID | None
    source_promotion_request_id: UUID | None
    created_by_id: UUID
    released_by_id: UUID | None
    released_at: datetime | None
    created_at: datetime
    updated_at: datetime


class RevisionStatusWrite(BaseModel):
    status: RevisionStatus


class CloneRevisionWrite(BaseModel):
    revision_code: str = Field(min_length=1, max_length=100)


class PromotionWrite(BaseModel):
    promotion_request_id: UUID
    revision_code: str = Field(min_length=1, max_length=100)
    variant_id: UUID | None = None


class BomItemWrite(BaseModel):
    component_id: UUID
    quantity: Decimal = Field(gt=0)
    uom_id: UUID | None = None
    position: str = Field(default="", max_length=100)
    sequence: int = Field(default=0, ge=0)
    required: bool = True
    notes: str = Field(default="", max_length=20000)


class BomItemRead(BomItemWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    revision_id: UUID
    uom_id: UUID
    created_at: datetime
    updated_at: datetime


class AlternativeWrite(BaseModel):
    component_id: UUID
    notes: str = Field(default="", max_length=20000)


class AlternativeRead(AlternativeWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    bom_item_id: UUID
    created_at: datetime
