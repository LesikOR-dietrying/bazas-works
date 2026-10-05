from datetime import date
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.models import Identity, Timestamps


class ProcurementStatus(StrEnum):
    REQUIRED = "REQUIRED"
    RFQ = "RFQ"
    ORDERED = "ORDERED"
    PAID = "PAID"
    IN_TRANSIT = "IN_TRANSIT"
    CUSTOMS = "CUSTOMS"
    RECEIVED = "RECEIVED"
    ISSUE = "ISSUE"


class Supplier(Identity, Timestamps, Base):
    __tablename__ = "suppliers"
    __table_args__ = (
        UniqueConstraint("name", name="uq_suppliers_name"),
        CheckConstraint("length(trim(name)) > 0", name="name_nonempty"),
    )
    name: Mapped[str] = mapped_column(String(255))
    contact_details: Mapped[str] = mapped_column(Text, default="", server_default="")
    notes: Mapped[str] = mapped_column(Text, default="", server_default="")


class ProcurementRecord(Identity, Timestamps, Base):
    __tablename__ = "procurement_records"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("unit_price IS NULL OR unit_price >= 0", name="price_nonnegative"),
        CheckConstraint(
            "status IN ('REQUIRED','RFQ','ORDERED','PAID','IN_TRANSIT',"
            "'CUSTOMS','RECEIVED','ISSUE')",
            name="status",
        ),
    )
    component_id: Mapped[UUID] = mapped_column(
        ForeignKey("components.id", ondelete="RESTRICT"), index=True
    )
    uom_id: Mapped[UUID] = mapped_column(
        ForeignKey("units_of_measure.id", ondelete="RESTRICT"), index=True
    )
    supplier_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("suppliers.id", ondelete="RESTRICT"), index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(16, 4))
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="UAH", server_default="UAH")
    order_date: Mapped[date | None] = mapped_column(Date)
    expected_date: Mapped[date | None] = mapped_column(Date)
    tracking_number: Mapped[str] = mapped_column(String(255), default="", server_default="")
    status: Mapped[str] = mapped_column(
        String(30),
        default=ProcurementStatus.REQUIRED,
        server_default=ProcurementStatus.REQUIRED,
        index=True,
    )
    notes: Mapped[str] = mapped_column(Text, default="", server_default="")
    created_by_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    component = relationship("Component", lazy="joined")
    uom = relationship("UnitOfMeasure", lazy="joined")
    supplier = relationship("Supplier", lazy="joined")

    @property
    def component_name(self) -> str:
        return self.component.name

    @property
    def supplier_name(self) -> str | None:
        return self.supplier.name if self.supplier else None

    @property
    def uom_code(self) -> str:
        return self.uom.code


class ProcurementAllocation(Identity, Base):
    __tablename__ = "procurement_allocations"
    __table_args__ = (
        UniqueConstraint(
            "procurement_record_id", "requirement_id", name="uq_procurement_allocations"
        ),
        CheckConstraint("quantity > 0", name="quantity_positive"),
    )
    procurement_record_id: Mapped[UUID] = mapped_column(
        ForeignKey("procurement_records.id", ondelete="CASCADE"), index=True
    )
    requirement_id: Mapped[UUID] = mapped_column(
        ForeignKey("material_requirements.id", ondelete="RESTRICT"), index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(16, 4))
