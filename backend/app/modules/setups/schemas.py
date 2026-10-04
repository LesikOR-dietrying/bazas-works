from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.pagination import ListParams
from app.modules.components.schemas import ComponentOption
from app.modules.setups.models import SetupStatus
from app.modules.users.schemas import Name

Measure = Annotated[Decimal, Field(ge=0, allow_inf_nan=False, max_digits=14, decimal_places=4)]


class SetupWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Name
    drone_class: Name
    version: Name
    status: SetupStatus = SetupStatus.DEVELOPMENT
    description: str = Field(default="", max_length=20000)
    weight_kg: Measure | None = None
    payload_kg: Measure | None = None
    battery_description: str = Field(default="", max_length=20000)
    battery_voltage: Measure | None = None
    battery_capacity_ah: Measure | None = None
    propeller_description: str = Field(default="", max_length=20000)
    flight_time_minutes: Measure | None = None
    average_current_a: Measure | None = None
    max_current_a: Measure | None = None
    firmware_type: str = Field(default="", max_length=255)
    firmware_version: str = Field(default="", max_length=255)
    notes: str = Field(default="", max_length=20000)
    attributes: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_current(self) -> Self:
        if (
            self.average_current_a is not None
            and self.max_current_a is not None
            and self.max_current_a < self.average_current_a
        ):
            raise ValueError("max_current_a must be at least average_current_a")
        return self


class SetupRead(SetupWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class SetupOption(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    version: str
    status: SetupStatus


class SetupFilters(ListParams):
    status: SetupStatus | None = None
    project_id: UUID | None = None
    component_id: UUID | None = None
    sort: Literal["name", "version", "status", "updated_at", "created_at"] = "updated_at"
    direction: Literal["asc", "desc"] = "desc"


class SetupClone(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Name


class SetupComponentWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    component_id: UUID
    quantity: int = Field(gt=0)
    position: str = Field(default="", max_length=100)
    notes: str = Field(default="", max_length=20000)


class SetupComponentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    setup_id: UUID
    component_id: UUID
    component: ComponentOption
    quantity: int
    position: str
    notes: str
    created_at: datetime
    updated_at: datetime
