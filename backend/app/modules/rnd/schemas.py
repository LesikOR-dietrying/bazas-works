from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.rnd.models import BranchStatus, ConfigurationRole, PromotionRequestStatus
from app.modules.setups.schemas import SetupOption
from app.modules.users.schemas import Name


class BranchWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Name
    parent_id: UUID | None = None
    responsible_user_id: UUID
    purpose: str = Field(default="", max_length=20000)
    change_summary: str = Field(default="", max_length=20000)
    result_summary: str = Field(default="", max_length=20000)


class BranchRead(BranchWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    status: BranchStatus
    responsible_name: str
    parent_name: str | None
    created_by_id: UUID
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class BranchTransition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: BranchStatus
    result_summary: str | None = Field(default=None, max_length=20000)


class BranchConfigurationWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    setup_id: UUID
    role: ConfigurationRole


class BranchConfigurationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    branch_id: UUID
    setup_id: UUID
    role: ConfigurationRole
    created_by_id: UUID
    created_at: datetime
    setup: SetupOption


class ConfigurationSummary(BaseModel):
    id: UUID
    name: str
    version: str
    status: str
    role: ConfigurationRole


class ValueChange(BaseModel):
    field: str
    baseline: object | None
    candidate: object | None


class BomChange(BaseModel):
    component_id: UUID
    component_name: str
    position: str
    baseline_quantity: int
    candidate_quantity: int


class ConfigurationComparison(BaseModel):
    baseline: ConfigurationSummary
    candidate: ConfigurationSummary
    attribute_changes: list[ValueChange]
    bom_changes: list[BomChange]


class PromotionRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_setup_id: UUID
    reason: str = Field(min_length=1, max_length=20000)


class PromotionRequestReview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: PromotionRequestStatus
    review_notes: str = Field(default="", max_length=20000)


class PromotionRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    branch_id: UUID
    candidate_setup_id: UUID
    candidate_name: str
    status: PromotionRequestStatus
    reason: str
    requested_by_id: UUID
    requested_by_name: str
    reviewed_by_id: UUID | None
    reviewed_by_name: str | None
    reviewed_at: datetime | None
    review_notes: str
    created_at: datetime
