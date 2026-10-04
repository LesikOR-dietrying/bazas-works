from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.pagination import ListParams
from app.modules.users.schemas import Name


class FirmwareWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    setup_id: UUID
    version_name: Name
    firmware_type: Name
    firmware_version: Name
    description: str = Field(default="", max_length=20000)
    config_text: str = Field(default="", max_length=200000)


class FirmwareRead(FirmwareWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    created_by_id: UUID


class FirmwareFilters(ListParams):
    setup_id: UUID | None = None


class ArtifactWrite(BaseModel):
    name: Name
    description: str = Field(default="", max_length=20000)


class ArtifactRead(ArtifactWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class ReleaseWrite(BaseModel):
    version: Name
    firmware_type: str = Field(default="", max_length=255)
    upstream_version: str = Field(default="", max_length=255)
    description: str = Field(default="", max_length=20000)
    config_text: str = Field(default="", max_length=200000)
    checksum: str = Field(default="", max_length=128)
    binary_attachment_id: UUID | None = None
    config_attachment_id: UUID | None = None


class ReleaseRead(ReleaseWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    artifact_id: UUID
    created_at: datetime
    created_by_id: UUID


class RequirementWrite(BaseModel):
    release_id: UUID
    purpose: Name
    notes: str = Field(default="", max_length=20000)
    configuration: dict[str, object] = Field(default_factory=dict)


class RequirementRead(RequirementWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    revision_id: UUID
    created_at: datetime
    updated_at: datetime
