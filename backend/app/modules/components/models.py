from enum import StrEnum
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import Identity, Timestamps


class ComponentCategory(StrEnum):
    MOTOR = "MOTOR"
    ESC = "ESC"
    FLIGHT_CONTROLLER = "FLIGHT_CONTROLLER"
    PROPELLER = "PROPELLER"
    BATTERY = "BATTERY"
    CAMERA = "CAMERA"
    VTX = "VTX"
    RX = "RX"
    GPS = "GPS"
    ANTENNA = "ANTENNA"
    FRAME = "FRAME"
    POWER_MODULE = "POWER_MODULE"
    OTHER = "OTHER"


class ComponentLifecycle(StrEnum):
    ACTIVE = "ACTIVE"
    OBSOLETE = "OBSOLETE"


class UnitOfMeasure(Identity, Timestamps, Base):
    __tablename__ = "units_of_measure"
    __table_args__ = (
        UniqueConstraint("code", name="uq_units_of_measure_code"),
        CheckConstraint("length(trim(code)) > 0", name="code_nonempty"),
        CheckConstraint("length(trim(name)) > 0", name="name_nonempty"),
        CheckConstraint("precision BETWEEN 0 AND 6", name="precision_range"),
    )

    code: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(100))
    precision: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class Component(Identity, Timestamps, Base):
    __tablename__ = "components"
    __table_args__ = (
        CheckConstraint(
            "category IN ('MOTOR','ESC','FLIGHT_CONTROLLER','PROPELLER','BATTERY',"
            "'CAMERA','VTX','RX','GPS','ANTENNA','FRAME','POWER_MODULE','OTHER')",
            name="category",
        ),
        CheckConstraint("length(trim(name)) > 0", name="name_nonempty"),
        CheckConstraint("jsonb_typeof(specifications) = 'object'", name="specifications_object"),
        Index("ix_components_manufacturer_model", "manufacturer", "model"),
    )

    category: Mapped[str] = mapped_column(String(32), index=True)
    sku: Mapped[str | None] = mapped_column(String(100), unique=True)
    lifecycle: Mapped[str] = mapped_column(
        String(20), default=ComponentLifecycle.ACTIVE, server_default=ComponentLifecycle.ACTIVE
    )
    default_uom_id: Mapped[UUID] = mapped_column(
        ForeignKey("units_of_measure.id", ondelete="RESTRICT"), index=True
    )
    manufacturer: Mapped[str] = mapped_column(String(255), default="", server_default="")
    model: Mapped[str] = mapped_column(String(255), default="", server_default="")
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    specifications: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )
    datasheet_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="", server_default="")
