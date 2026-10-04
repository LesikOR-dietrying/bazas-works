from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, ValidationInfo, field_validator

from app.core.pagination import ListParams
from app.modules.components.models import ComponentCategory, ComponentLifecycle
from app.modules.users.schemas import Name


class ComponentWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: ComponentCategory
    sku: str | None = Field(default=None, max_length=100)
    lifecycle: ComponentLifecycle = ComponentLifecycle.ACTIVE
    default_uom_id: UUID | None = None
    manufacturer: str = Field(default="", max_length=255)
    model: str = Field(default="", max_length=255)
    name: Name
    description: str = Field(default="", max_length=20000)
    specifications: dict[str, object] = Field(default_factory=dict)
    datasheet_url: HttpUrl | None = None
    notes: str = Field(default="", max_length=20000)

    @field_validator("specifications")
    @classmethod
    def validate_known_specs(
        cls, specs: dict[str, object], info: ValidationInfo
    ) -> dict[str, object]:
        from decimal import Decimal, InvalidOperation

        category = info.data.get("category")
        numeric = {
            ComponentCategory.MOTOR: {"kv", "weight_g", "max_current_a", "max_power_w"},
            ComponentCategory.ESC: {"continuous_current_a", "burst_current_a"},
        }.get(category, set())
        for key in numeric:
            if key not in specs:
                continue
            value = specs[key]
            if isinstance(value, bool) or not isinstance(value, (int, float, str)):
                raise ValueError(f"{key} must be a non-negative finite number")
            try:
                number = Decimal(str(value))
            except InvalidOperation as exc:
                raise ValueError(f"{key} must be a non-negative finite number") from exc
            if not number.is_finite() or number < 0:
                raise ValueError(f"{key} must be a non-negative finite number")
        if "voltage" in specs and category in {ComponentCategory.MOTOR, ComponentCategory.ESC}:
            voltage = specs["voltage"]
            if isinstance(voltage, bool) or not isinstance(voltage, (int, float, str)):
                raise ValueError("voltage must be a string or a non-negative finite number")
            if isinstance(voltage, str) and not voltage.strip():
                raise ValueError("voltage must not be blank")
            if isinstance(voltage, (int, float)) and (
                not Decimal(str(voltage)).is_finite() or voltage < 0
            ):
                raise ValueError("voltage must be non-negative and finite")
        if category == ComponentCategory.MOTOR and "recommended_propellers" in specs:
            props = specs["recommended_propellers"]
            if not isinstance(props, list) or not all(
                isinstance(value, str) and value.strip() for value in props
            ):
                raise ValueError("recommended_propellers must be a list of non-empty strings")
        if category == ComponentCategory.ESC and "firmware" in specs:
            firmware = specs["firmware"]
            if not isinstance(firmware, str) or not firmware.strip():
                raise ValueError("firmware must be a non-empty string")
        return specs


class ComponentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    category: ComponentCategory
    sku: str | None
    lifecycle: ComponentLifecycle
    default_uom_id: UUID
    manufacturer: str
    model: str
    name: str
    description: str
    specifications: dict[str, object]
    datasheet_url: str | None
    notes: str
    created_at: datetime
    updated_at: datetime


class ComponentOption(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    category: ComponentCategory
    sku: str | None
    lifecycle: ComponentLifecycle
    default_uom_id: UUID
    manufacturer: str
    model: str
    name: str


class ComponentFilters(ListParams):
    category: ComponentCategory | None = None
    sort: Literal["name", "category", "manufacturer", "model", "updated_at", "created_at"] = (
        "updated_at"
    )
    direction: Literal["asc", "desc"] = "desc"


class UnitOfMeasureRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    code: str
    name: str
    precision: int
