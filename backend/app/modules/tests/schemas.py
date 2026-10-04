import json
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from app.core.pagination import ListParams
from app.modules.components.schemas import ComponentOption
from app.modules.tests.models import TestComponentRole, TestStatus, TestType
from app.modules.users.schemas import Name

NonNegative = Annotated[Decimal, Field(ge=0, allow_inf_nan=False, max_digits=14, decimal_places=4)]
Temperature = Annotated[Decimal, Field(allow_inf_nan=False, max_digits=14, decimal_places=4)]
Throttle = Annotated[
    Decimal, Field(ge=0, le=100, allow_inf_nan=False, max_digits=14, decimal_places=4)
]


class TestWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Name
    test_type: TestType
    project_id: UUID | None = None
    branch_id: UUID | None = None
    setup_id: UUID | None = None
    component_id: UUID | None = None
    firmware_revision_id: UUID | None = None
    performed_by_id: UUID | None = None
    test_date: AwareDatetime | None = None
    status: TestStatus = TestStatus.PLANNED
    description: str = Field(default="", max_length=20000)
    conditions: dict[str, object] = Field(default_factory=dict)
    result_summary: dict[str, object] = Field(default_factory=dict)
    conclusion: str = Field(default="", max_length=20000)

    @model_validator(mode="after")
    def validate_relations(self) -> Self:
        if not (self.project_id or self.setup_id or self.component_id):
            raise ValueError("A test needs a project, setup or component")
        if self.test_type in {TestType.FLIGHT, TestType.ENDURANCE} and not self.setup_id:
            raise ValueError("Flight and endurance tests need a setup")
        if self.test_type == TestType.MOTOR_BENCH and not self.component_id:
            raise ValueError("Motor bench tests need a motor component")
        if self.firmware_revision_id and not self.setup_id:
            raise ValueError("Firmware revision needs a setup")
        if self.status != TestStatus.PLANNED and not (self.performed_by_id and self.test_date):
            raise ValueError("Executed tests need an operator and a date")
        for field in ("conditions", "result_summary"):
            try:
                json.dumps(getattr(self, field), allow_nan=False)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{field} must contain finite JSON values") from exc
        return self


class TestRead(TestWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class TestFilters(ListParams):
    project_id: UUID | None = None
    branch_id: UUID | None = None
    setup_id: UUID | None = None
    component_id: UUID | None = None
    test_type: TestType | None = None
    status: TestStatus | None = None
    sort: Literal["name", "test_type", "status", "test_date", "updated_at", "created_at"] = (
        "test_date"
    )
    direction: Literal["asc", "desc"] = "desc"


class TestComponentWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    component_id: UUID
    role: TestComponentRole
    notes: str = Field(default="", max_length=20000)


class TestComponentRead(TestComponentWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    test_id: UUID
    component: ComponentOption
    created_at: datetime


class TestMeasurementWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sequence: int = Field(ge=0)
    throttle_percent: Throttle | None = None
    voltage_v: NonNegative | None = None
    current_a: NonNegative | None = None
    power_w: NonNegative | None = None
    rpm: NonNegative | None = None
    thrust_kg: NonNegative | None = None
    efficiency_g_w: NonNegative | None = None
    motor_temperature_c: Temperature | None = None
    esc_temperature_c: Temperature | None = None
    timestamp_seconds: NonNegative | None = None


class TestMeasurementRead(TestMeasurementWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    test_id: UUID
    created_at: datetime
    updated_at: datetime
