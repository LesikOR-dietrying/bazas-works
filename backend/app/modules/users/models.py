from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.models import Identity, Timestamps


class Role(StrEnum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    ENGINEER = "ENGINEER"
    EMPLOYEE = "EMPLOYEE"


class RoleCode(StrEnum):
    ADMINISTRATOR = "ADMINISTRATOR"
    ENGINEER = "ENGINEER"
    RND_ENGINEER = "RND_ENGINEER"
    PRODUCTION_MANAGER = "PRODUCTION_MANAGER"
    PROCUREMENT_SPECIALIST = "PROCUREMENT_SPECIALIST"
    ASSEMBLER = "ASSEMBLER"
    ELECTRONICS_TECHNICIAN = "ELECTRONICS_TECHNICIAN"
    FIRMWARE_ENGINEER = "FIRMWARE_ENGINEER"
    TEST_PILOT = "TEST_PILOT"
    TEST_ENGINEER = "TEST_ENGINEER"
    QUALITY_CONTROLLER = "QUALITY_CONTROLLER"


class User(Identity, Timestamps, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('ADMIN','MANAGER','ENGINEER','EMPLOYEE')", name="role"),
        CheckConstraint("length(trim(full_name)) > 0", name="full_name_nonempty"),
        CheckConstraint("length(trim(username)) > 0", name="username_nonempty"),
    )
    username: Mapped[str] = mapped_column(String(320))
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    role: Mapped[str] = mapped_column(String(20), default=Role.EMPLOYEE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    role_assignments: Mapped[list[UserRole]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="UserRole.user_id",
        lazy="selectin",
    )

    @property
    def roles(self) -> list[RoleCode]:
        return sorted((RoleCode(item.role.code) for item in self.role_assignments), key=str)

    @property
    def capabilities(self) -> list[str]:
        from app.modules.users.permissions import capabilities_for

        return sorted(capability.value for capability in capabilities_for(self))


class RoleDefinition(Identity, Base):
    __tablename__ = "roles"
    __table_args__ = (
        CheckConstraint("length(trim(code)) > 0", name="code_nonempty"),
        CheckConstraint("length(trim(name)) > 0", name="name_nonempty"),
        UniqueConstraint("code", name="uq_roles_code"),
    )
    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class UserRole(Identity, Base):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_id_role_id"),)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), index=True)
    assigned_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    user: Mapped[User] = relationship(back_populates="role_assignments", foreign_keys=[user_id])
    role: Mapped[RoleDefinition] = relationship(lazy="joined")


Index("uq_users_email_lower", func.lower(User.email), unique=True)
Index("uq_users_username_lower", func.lower(User.username), unique=True)
