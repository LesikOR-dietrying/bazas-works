from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.models import Identity, Timestamps
from app.modules.components.models import Component


class SetupStatus(StrEnum):
    DEVELOPMENT = "DEVELOPMENT"
    TESTING = "TESTING"
    READY = "READY"
    DEPRECATED = "DEPRECATED"


class Setup(Identity, Timestamps, Base):
    __tablename__ = "setups"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_setups_name_version"),
        CheckConstraint("status IN ('DEVELOPMENT','TESTING','READY','DEPRECATED')", name="status"),
        CheckConstraint("length(trim(name)) > 0", name="name_nonempty"),
        CheckConstraint("length(trim(version)) > 0", name="version_nonempty"),
        CheckConstraint("length(trim(drone_class)) > 0", name="drone_class_nonempty"),
        CheckConstraint("weight_kg IS NULL OR weight_kg >= 0", name="weight_nonnegative"),
        CheckConstraint("payload_kg IS NULL OR payload_kg >= 0", name="payload_nonnegative"),
        CheckConstraint(
            "battery_voltage IS NULL OR battery_voltage >= 0", name="battery_voltage_nonnegative"
        ),
        CheckConstraint(
            "battery_capacity_ah IS NULL OR battery_capacity_ah >= 0",
            name="battery_capacity_nonnegative",
        ),
        CheckConstraint(
            "flight_time_minutes IS NULL OR flight_time_minutes >= 0",
            name="flight_time_nonnegative",
        ),
        CheckConstraint(
            "average_current_a IS NULL OR average_current_a >= 0",
            name="average_current_nonnegative",
        ),
        CheckConstraint(
            "max_current_a IS NULL OR max_current_a >= 0", name="max_current_nonnegative"
        ),
        CheckConstraint(
            "average_current_a IS NULL OR max_current_a IS NULL OR "
            "max_current_a >= average_current_a",
            name="current_order",
        ),
    )

    name: Mapped[str] = mapped_column(String(255))
    drone_class: Mapped[str] = mapped_column(String(255))
    version: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default=SetupStatus.DEVELOPMENT, index=True)
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    payload_kg: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    battery_description: Mapped[str] = mapped_column(Text, default="", server_default="")
    battery_voltage: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    battery_capacity_ah: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    propeller_description: Mapped[str] = mapped_column(Text, default="", server_default="")
    flight_time_minutes: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    average_current_a: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    max_current_a: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    firmware_type: Mapped[str] = mapped_column(String(255), default="", server_default="")
    firmware_version: Mapped[str] = mapped_column(String(255), default="", server_default="")
    notes: Mapped[str] = mapped_column(Text, default="", server_default="")
    attributes: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict, server_default="{}")
    components: Mapped[list[SetupComponent]] = relationship(
        back_populates="setup", cascade="all, delete-orphan", lazy="selectin", passive_deletes=True
    )


class SetupComponent(Identity, Timestamps, Base):
    __tablename__ = "setup_components"
    __table_args__ = (
        UniqueConstraint(
            "setup_id",
            "component_id",
            "position",
            name="uq_setup_components_setup_component_position",
        ),
        CheckConstraint("quantity > 0", name="quantity_positive"),
    )

    setup_id: Mapped[UUID] = mapped_column(ForeignKey("setups.id", ondelete="CASCADE"))
    component_id: Mapped[UUID] = mapped_column(
        ForeignKey("components.id", ondelete="RESTRICT"), index=True
    )
    quantity: Mapped[int] = mapped_column(Integer)
    position: Mapped[str] = mapped_column(String(100), default="", server_default="")
    notes: Mapped[str] = mapped_column(Text, default="", server_default="")
    setup: Mapped[Setup] = relationship(back_populates="components")
    component: Mapped[Component] = relationship(lazy="joined")


class ProjectSetup(Identity, Base):
    __tablename__ = "project_setups"
    __table_args__ = (
        UniqueConstraint("project_id", "setup_id", name="uq_project_setups_project_setup_pair"),
        Index("ix_project_setups_setup_id", "setup_id"),
    )
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    setup_id: Mapped[UUID] = mapped_column(ForeignKey("setups.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    setup: Mapped[Setup] = relationship(lazy="joined")
