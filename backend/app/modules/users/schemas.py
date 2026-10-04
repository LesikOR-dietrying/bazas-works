from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, StringConstraints

from app.core.pagination import ListParams
from app.modules.users.models import Role, RoleCode

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
Username = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, to_lower=True, min_length=1, max_length=320, pattern=r"^\S+$"
    ),
]
Password = Annotated[SecretStr, Field(min_length=12, max_length=128)]


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    full_name: Name
    username: Username
    email: EmailStr | None = None
    password: Password
    roles: list[RoleCode] = Field(default_factory=list)


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    full_name: Name
    username: Username
    email: EmailStr | None
    roles: list[RoleCode]
    is_active: bool


class PasswordReset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: Password


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    username: str
    full_name: str
    email: str | None
    role: Role
    roles: list[RoleCode]
    capabilities: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserOption(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    full_name: str


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    code: RoleCode
    name: str


class UserFilters(ListParams):
    role: RoleCode | None = None
    is_active: bool | None = None
