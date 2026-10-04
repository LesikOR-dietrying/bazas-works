from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
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


class OrderStatus(StrEnum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    MATERIALS = "MATERIALS"
    PRODUCTION = "PRODUCTION"
    READY = "READY"
    PARTIALLY_SHIPPED = "PARTIALLY_SHIPPED"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


class VariantStatus(StrEnum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RELEASED = "RELEASED"


class Customer(Identity, Timestamps, Base):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("name", name="uq_customers_name"),
        CheckConstraint("length(trim(name)) > 0", name="name_nonempty"),
    )
    name: Mapped[str] = mapped_column(String(255))
    contact_details: Mapped[str] = mapped_column(Text, default="", server_default="")
    notes: Mapped[str] = mapped_column(Text, default="", server_default="")


class Order(Identity, Timestamps, Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("order_number", name="uq_orders_number"),
        CheckConstraint("length(trim(order_number)) > 0", name="number_nonempty"),
        CheckConstraint(
            "status IN ('DRAFT','CONFIRMED','MATERIALS','PRODUCTION','READY',"
            "'PARTIALLY_SHIPPED','SHIPPED','CANCELLED')",
            name="status",
        ),
        CheckConstraint("deadline IS NULL OR deadline >= order_date", name="date_order"),
    )
    order_number: Mapped[str] = mapped_column(String(100))
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), index=True
    )
    recipient: Mapped[str] = mapped_column(String(255), default="", server_default="")
    destination: Mapped[str] = mapped_column(Text, default="", server_default="")
    order_date: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    deadline: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(
        String(30), default=OrderStatus.DRAFT, server_default=OrderStatus.DRAFT, index=True
    )
    notes: Mapped[str] = mapped_column(Text, default="", server_default="")
    created_by_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    customer: Mapped[Customer] = relationship(lazy="joined")

    @property
    def customer_name(self) -> str:
        return self.customer.name


class OrderItem(Identity, Timestamps, Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        UniqueConstraint(
            "order_id", "product_revision_id", "required_date", name="uq_order_items_line"
        ),
    )
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"))
    product_revision_id: Mapped[UUID] = mapped_column(
        ForeignKey("product_revisions.id", ondelete="RESTRICT"), index=True
    )
    quantity: Mapped[int] = mapped_column(Integer)
    required_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str] = mapped_column(Text, default="", server_default="")
    product = relationship("Product", lazy="joined")
    product_revision = relationship("ProductRevision", lazy="joined")

    @property
    def product_name(self) -> str:
        return self.product.name

    @property
    def revision_code(self) -> str:
        return self.product_revision.revision_code


class OrderVariant(Identity, Timestamps, Base):
    __tablename__ = "order_variants"
    __table_args__ = (
        UniqueConstraint("order_item_id", "name", name="uq_order_variants_name"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint(
            "status IN ('DRAFT','PENDING_APPROVAL','APPROVED','REJECTED','RELEASED')", name="status"
        ),
    )
    order_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("order_items.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    quantity: Mapped[int] = mapped_column(Integer)
    is_standard: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    status: Mapped[str] = mapped_column(
        String(30), default=VariantStatus.DRAFT, server_default=VariantStatus.DRAFT, index=True
    )
    notes: Mapped[str] = mapped_column(Text, default="", server_default="")


class VariantDeviation(Identity, Base):
    __tablename__ = "variant_deviations"
    __table_args__ = (
        UniqueConstraint("variant_id", "original_bom_item_id", name="uq_variant_deviations_bom"),
        CheckConstraint("quantity_per_product > 0", name="quantity_positive"),
        CheckConstraint("length(trim(reason)) > 0", name="reason_nonempty"),
    )
    variant_id: Mapped[UUID] = mapped_column(
        ForeignKey("order_variants.id", ondelete="CASCADE"), index=True
    )
    original_bom_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("product_revision_bom_items.id", ondelete="RESTRICT")
    )
    replacement_component_id: Mapped[UUID] = mapped_column(
        ForeignKey("components.id", ondelete="RESTRICT"), index=True
    )
    quantity_per_product: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    reason: Mapped[str] = mapped_column(Text)
    requested_by_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    approved_by_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str] = mapped_column(Text, default="", server_default="")
    required_retest: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DeviationTest(Identity, Base):
    __tablename__ = "deviation_tests"
    __table_args__ = (UniqueConstraint("deviation_id", "test_id", name="uq_deviation_tests"),)
    deviation_id: Mapped[UUID] = mapped_column(
        ForeignKey("variant_deviations.id", ondelete="CASCADE")
    )
    test_id: Mapped[UUID] = mapped_column(ForeignKey("tests.id", ondelete="RESTRICT"))


class MaterialRequirement(Identity, Timestamps, Base):
    __tablename__ = "material_requirements"
    __table_args__ = (
        UniqueConstraint("variant_id", "original_bom_item_id", name="uq_material_requirements_bom"),
        CheckConstraint("required_quantity > 0", name="quantity_positive"),
    )
    variant_id: Mapped[UUID] = mapped_column(
        ForeignKey("order_variants.id", ondelete="CASCADE"), index=True
    )
    original_bom_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("product_revision_bom_items.id", ondelete="RESTRICT")
    )
    source_deviation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("variant_deviations.id", ondelete="RESTRICT")
    )
    component_id: Mapped[UUID] = mapped_column(
        ForeignKey("components.id", ondelete="RESTRICT"), index=True
    )
    uom_id: Mapped[UUID] = mapped_column(ForeignKey("units_of_measure.id", ondelete="RESTRICT"))
    required_quantity: Mapped[Decimal] = mapped_column(Numeric(16, 4))
    component = relationship("Component", lazy="joined")

    @property
    def component_name(self) -> str:
        return self.component.name
