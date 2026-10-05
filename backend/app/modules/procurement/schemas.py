from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.pagination import ListParams
from app.modules.procurement.models import ProcurementStatus


class SupplierWrite(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    contact_details: str = ""
    notes: str = ""


class SupplierRead(SupplierWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class ProcurementWrite(BaseModel):
    component_id: UUID
    supplier_id: UUID | None = None
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="UAH", min_length=3, max_length=3)
    order_date: date | None = None
    expected_date: date | None = None
    tracking_number: str = ""
    status: ProcurementStatus = ProcurementStatus.REQUIRED
    notes: str = ""


class ProcurementRead(ProcurementWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_by_id: UUID
    component_name: str
    uom_id: UUID
    uom_code: str
    supplier_name: str | None
    created_at: datetime
    updated_at: datetime


class ProcurementFilters(ListParams):
    component_id: UUID | None = None
    status: ProcurementStatus | None = None


class ProcurementStatusWrite(BaseModel):
    status: ProcurementStatus


class AllocationWrite(BaseModel):
    requirement_id: UUID
    quantity: Decimal = Field(gt=0)


class AllocationRead(AllocationWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    procurement_record_id: UUID
