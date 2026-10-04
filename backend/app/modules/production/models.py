from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.models import Identity, Timestamps


class ExecutionStatus(StrEnum):
    WAITING = "WAITING"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    PASSED = "PASSED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class StageEventType(StrEnum):
    START = "START"
    PASS = "PASS"
    FAIL = "FAIL"
    RETURN = "RETURN"
    CANCEL = "CANCEL"


class ProductionItem(Identity, Timestamps, Base):
    __tablename__ = "production_items"
    __table_args__ = (
        UniqueConstraint("identifier", name="uq_production_items_identifier"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("tracking_mode IN ('SERIAL','BATCH','QUANTITY')", name="tracking_mode"),
        CheckConstraint(
            "(tracking_mode = 'SERIAL' AND quantity = 1) OR tracking_mode IN ('BATCH','QUANTITY')",
            name="serial_quantity",
        ),
    )
    variant_id: Mapped[UUID] = mapped_column(
        ForeignKey("order_variants.id", ondelete="RESTRICT"), index=True
    )
    route_id: Mapped[UUID] = mapped_column(
        ForeignKey("production_routes.id", ondelete="RESTRICT"), index=True
    )
    tracking_mode: Mapped[str] = mapped_column(String(20))
    identifier: Mapped[str] = mapped_column(String(180))
    quantity: Mapped[int] = mapped_column(Integer)


class StageExecution(Identity, Timestamps, Base):
    __tablename__ = "stage_executions"
    __table_args__ = (
        UniqueConstraint("production_item_id", "stage_id", "attempt", name="uq_stage_attempt"),
        CheckConstraint("attempt > 0", name="attempt_positive"),
        CheckConstraint("planned_quantity > 0", name="planned_positive"),
        CheckConstraint("completed_quantity >= 0", name="completed_nonnegative"),
        CheckConstraint("failed_quantity >= 0", name="failed_nonnegative"),
        CheckConstraint(
            "completed_quantity + failed_quantity <= planned_quantity", name="result_within_plan"
        ),
        CheckConstraint(
            "status IN ('WAITING','READY','IN_PROGRESS','PASSED','FAILED','CANCELLED')",
            name="status",
        ),
    )
    production_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("production_items.id", ondelete="RESTRICT"), index=True
    )
    stage_id: Mapped[UUID] = mapped_column(
        ForeignKey("route_stages.id", ondelete="RESTRICT"), index=True
    )
    attempt: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    planned_quantity: Mapped[int] = mapped_column(Integer)
    completed_quantity: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    failed_quantity: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    status: Mapped[str] = mapped_column(String(20), index=True)
    assigned_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    started_by_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    result_note: Mapped[str] = mapped_column(Text, default="", server_default="")
    item: Mapped[ProductionItem] = relationship(lazy="joined")
    stage = relationship("RouteStage", lazy="joined")


class StageChecklistResult(Identity, Base):
    __tablename__ = "stage_checklist_results"
    __table_args__ = (
        UniqueConstraint("execution_id", "template_item_id", name="uq_execution_checklist_item"),
    )
    execution_id: Mapped[UUID] = mapped_column(
        ForeignKey("stage_executions.id", ondelete="CASCADE"), index=True
    )
    template_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("checklist_template_items.id", ondelete="RESTRICT")
    )
    text_snapshot: Mapped[str] = mapped_column(Text)
    required_snapshot: Mapped[bool] = mapped_column(Boolean)
    note_required_snapshot: Mapped[bool] = mapped_column(Boolean)
    photo_required_snapshot: Mapped[bool] = mapped_column(Boolean)
    checked: Mapped[bool] = mapped_column(Boolean)
    note: Mapped[str] = mapped_column(Text, default="", server_default="")
    photo_attachment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("attachments.id", ondelete="RESTRICT")
    )
    completed_by_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class StageEvent(Identity, Base):
    __tablename__ = "stage_events"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_stage_events_idempotency_key"),
        CheckConstraint("event_type IN ('START','PASS','FAIL','RETURN','CANCEL')", name="type"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
    )
    execution_id: Mapped[UUID] = mapped_column(
        ForeignKey("stage_executions.id", ondelete="RESTRICT"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(20))
    quantity: Mapped[Decimal] = mapped_column(Numeric(16, 4))
    reason: Mapped[str] = mapped_column(Text, default="", server_default="")
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    idempotency_key: Mapped[UUID | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
