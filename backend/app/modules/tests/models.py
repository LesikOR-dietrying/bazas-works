from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
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


class TestStatus(StrEnum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"


class TestType(StrEnum):
    MOTOR_BENCH = "MOTOR_BENCH"
    ESC_BENCH = "ESC_BENCH"
    BATTERY = "BATTERY"
    PROPELLER = "PROPELLER"
    FLIGHT = "FLIGHT"
    ENDURANCE = "ENDURANCE"
    RANGE = "RANGE"
    TEMPERATURE = "TEMPERATURE"
    FRAME = "FRAME"
    ANTENNA = "ANTENNA"
    OTHER = "OTHER"


class TestComponentRole(StrEnum):
    ESC = "ESC"
    PROPELLER = "PROPELLER"
    BATTERY = "BATTERY"
    OTHER = "OTHER"


class Test(Identity, Timestamps, Base):
    __tablename__ = "tests"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "setup_id"],
            ["project_setups.project_id", "project_setups.setup_id"],
            name="fk_tests_project_setup_project_setups",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["setup_id", "firmware_revision_id"],
            ["firmware_revisions.setup_id", "firmware_revisions.id"],
            name="fk_tests_setup_firmware_firmware_revisions",
            ondelete="RESTRICT",
        ),
        CheckConstraint("length(trim(name)) > 0", name="name_nonempty"),
        CheckConstraint(
            "branch_id IS NULL OR project_id IS NOT NULL", name="branch_requires_project"
        ),
        ForeignKeyConstraint(
            ["project_id", "branch_id"],
            ["rd_branches.project_id", "rd_branches.id"],
            name="fk_tests_project_branch_rd_branches",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "test_type IN ('MOTOR_BENCH','ESC_BENCH','BATTERY','PROPELLER','FLIGHT',"
            "'ENDURANCE','RANGE','TEMPERATURE','FRAME','ANTENNA','OTHER')",
            name="test_type",
        ),
        CheckConstraint(
            "status IN ('PLANNED','IN_PROGRESS','PASS','FAIL','PARTIAL')", name="status"
        ),
        CheckConstraint(
            "project_id IS NOT NULL OR setup_id IS NOT NULL OR component_id IS NOT NULL",
            name="has_subject",
        ),
        CheckConstraint(
            "firmware_revision_id IS NULL OR setup_id IS NOT NULL", name="firmware_needs_setup"
        ),
        CheckConstraint(
            "test_type NOT IN ('FLIGHT','ENDURANCE') OR setup_id IS NOT NULL",
            name="flight_needs_setup",
        ),
        CheckConstraint(
            "test_type != 'MOTOR_BENCH' OR component_id IS NOT NULL",
            name="motor_needs_component",
        ),
        CheckConstraint(
            "status = 'PLANNED' OR (performed_by_id IS NOT NULL AND test_date IS NOT NULL)",
            name="performed_when_executed",
        ),
        CheckConstraint("jsonb_typeof(conditions) = 'object'", name="conditions_object"),
        CheckConstraint("jsonb_typeof(result_summary) = 'object'", name="result_summary_object"),
        Index("ix_tests_test_type_test_date", "test_type", "test_date"),
        Index("ix_tests_status_test_date", "status", "test_date"),
        Index("ix_tests_setup_test_date", "setup_id", "test_date"),
        Index("ix_tests_component_test_date", "component_id", "test_date"),
    )

    name: Mapped[str] = mapped_column(String(255))
    test_type: Mapped[str] = mapped_column(String(32))
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), index=True
    )
    branch_id: Mapped[UUID | None] = mapped_column(index=True)
    setup_id: Mapped[UUID | None] = mapped_column(ForeignKey("setups.id", ondelete="RESTRICT"))
    component_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("components.id", ondelete="RESTRICT")
    )
    firmware_revision_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("firmware_revisions.id", ondelete="RESTRICT"), index=True
    )
    performed_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    test_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default=TestStatus.PLANNED)
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    conditions: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict, server_default="{}")
    result_summary: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )
    conclusion: Mapped[str] = mapped_column(Text, default="", server_default="")
    equipment: Mapped[list[TestComponent]] = relationship(
        back_populates="test", cascade="all, delete-orphan", passive_deletes=True
    )
    measurements: Mapped[list[TestMeasurement]] = relationship(
        back_populates="test", cascade="all, delete-orphan", passive_deletes=True
    )


class TestComponent(Identity, Base):
    __tablename__ = "test_components"
    __table_args__ = (
        UniqueConstraint(
            "test_id", "component_id", "role", name="uq_test_components_test_component_role"
        ),
        CheckConstraint("role IN ('ESC','PROPELLER','BATTERY','OTHER')", name="role"),
    )

    test_id: Mapped[UUID] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"))
    component_id: Mapped[UUID] = mapped_column(
        ForeignKey("components.id", ondelete="RESTRICT"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))
    notes: Mapped[str] = mapped_column(Text, default="", server_default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    test: Mapped[Test] = relationship(back_populates="equipment")
    component: Mapped[Component] = relationship(lazy="joined")


class TestMeasurement(Identity, Timestamps, Base):
    __tablename__ = "test_measurements"
    __table_args__ = (
        UniqueConstraint("test_id", "sequence", name="uq_test_measurements_test_sequence"),
        CheckConstraint("sequence >= 0", name="sequence_nonnegative"),
        CheckConstraint(
            "throttle_percent IS NULL OR (throttle_percent BETWEEN 0 AND 100 "
            "AND throttle_percent::text NOT IN ('NaN','Infinity','-Infinity'))",
            name="throttle_range",
        ),
        *(
            CheckConstraint(
                f"{field} IS NULL OR ({field} >= 0 AND "
                f"{field}::text NOT IN ('NaN','Infinity','-Infinity'))",
                name=f"{field}_nonnegative",
            )
            for field in (
                "voltage_v",
                "current_a",
                "power_w",
                "rpm",
                "thrust_kg",
                "efficiency_g_w",
                "timestamp_seconds",
            )
        ),
        *(
            CheckConstraint(
                f"{field} IS NULL OR {field}::text NOT IN ('NaN','Infinity','-Infinity')",
                name=f"{field}_finite",
            )
            for field in ("motor_temperature_c", "esc_temperature_c")
        ),
    )
    test_id: Mapped[UUID] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"))
    sequence: Mapped[int] = mapped_column(Integer)
    throttle_percent: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    voltage_v: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    current_a: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    power_w: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    rpm: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    thrust_kg: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    efficiency_g_w: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    motor_temperature_c: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    esc_temperature_c: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    timestamp_seconds: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    test: Mapped[Test] = relationship(back_populates="measurements")
