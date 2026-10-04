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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.models import Identity, Timestamps


class ProductLifecycle(StrEnum):
    DEVELOPMENT = "DEVELOPMENT"
    PRODUCTION = "PRODUCTION"
    DEPRECATED = "DEPRECATED"


class TrackingMode(StrEnum):
    SERIAL = "SERIAL"
    BATCH = "BATCH"
    QUANTITY = "QUANTITY"


class RevisionStatus(StrEnum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    RELEASED = "RELEASED"
    RETIRED = "RETIRED"


class ProductDocumentType(StrEnum):
    USER_MANUAL = "USER_MANUAL"
    MANUFACTURING = "MANUFACTURING"
    CONFIGURATION = "CONFIGURATION"
    DRAWING = "DRAWING"
    WIRING_DIAGRAM = "WIRING_DIAGRAM"
    OTHER = "OTHER"


class ProductCategory(Identity, Timestamps, Base):
    __tablename__ = "product_categories"
    __table_args__ = (
        UniqueConstraint("code", name="uq_product_categories_code"),
        CheckConstraint("length(trim(code)) > 0", name="code_nonempty"),
        CheckConstraint("length(trim(name)) > 0", name="name_nonempty"),
    )

    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class Product(Identity, Timestamps, Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("code", name="uq_products_code"),
        CheckConstraint("length(trim(code)) > 0", name="code_nonempty"),
        CheckConstraint("length(trim(name)) > 0", name="name_nonempty"),
        CheckConstraint("lifecycle IN ('DEVELOPMENT','PRODUCTION','DEPRECATED')", name="lifecycle"),
        CheckConstraint("tracking_mode IN ('SERIAL','BATCH','QUANTITY')", name="tracking_mode"),
    )

    code: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(255))
    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("product_categories.id", ondelete="RESTRICT"), index=True
    )
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    lifecycle: Mapped[str] = mapped_column(
        String(20),
        default=ProductLifecycle.DEVELOPMENT,
        server_default=ProductLifecycle.DEVELOPMENT,
    )
    tracking_mode: Mapped[str] = mapped_column(String(20))
    current_revision_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "product_revisions.id",
            ondelete="RESTRICT",
            use_alter=True,
            name="fk_products_current_revision_id_product_revisions",
        ),
        index=True,
    )
    general_image_attachment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "attachments.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_products_general_image_attachment_id_attachments",
        )
    )
    category: Mapped[ProductCategory] = relationship(lazy="joined")

    @property
    def category_name(self) -> str:
        return self.category.name


class ProductRevision(Identity, Timestamps, Base):
    __tablename__ = "product_revisions"
    __table_args__ = (
        UniqueConstraint("product_id", "id", name="uq_product_revisions_product_id_pair"),
        UniqueConstraint("product_id", "revision_code", name="uq_product_revisions_product_code"),
        UniqueConstraint("source_promotion_request_id", name="uq_product_revisions_promotion"),
        CheckConstraint("length(trim(revision_code)) > 0", name="revision_code_nonempty"),
        CheckConstraint("status IN ('DRAFT','IN_REVIEW','RELEASED','RETIRED')", name="status"),
        CheckConstraint("standard_cost IS NULL OR standard_cost >= 0", name="cost_nonnegative"),
        CheckConstraint(
            "jsonb_typeof(technical_characteristics) = 'object'", name="technical_object"
        ),
        CheckConstraint(
            "(status IN ('RELEASED','RETIRED')) = (released_at IS NOT NULL)",
            name="release_state",
        ),
    )

    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"))
    revision_code: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(
        String(20), default=RevisionStatus.DRAFT, server_default=RevisionStatus.DRAFT, index=True
    )
    source_project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), index=True
    )
    source_branch_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("rd_branches.id", ondelete="RESTRICT"), index=True
    )
    source_setup_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("setups.id", ondelete="RESTRICT"), index=True
    )
    source_promotion_request_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("rnd_promotion_requests.id", ondelete="RESTRICT")
    )
    technical_characteristics: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )
    standard_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="UAH", server_default="UAH")
    revision_instructions: Mapped[str] = mapped_column(Text, default="", server_default="")
    created_by_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    released_by_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    product: Mapped[Product] = relationship(lazy="joined", foreign_keys=[product_id])

    @property
    def product_name(self) -> str:
        return self.product.name


class ProductRevisionBomItem(Identity, Timestamps, Base):
    __tablename__ = "product_revision_bom_items"
    __table_args__ = (
        UniqueConstraint(
            "revision_id", "component_id", "position", name="uq_revision_bom_component_position"
        ),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("sequence >= 0", name="sequence_nonnegative"),
    )

    revision_id: Mapped[UUID] = mapped_column(
        ForeignKey("product_revisions.id", ondelete="CASCADE"), index=True
    )
    component_id: Mapped[UUID] = mapped_column(
        ForeignKey("components.id", ondelete="RESTRICT"), index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    uom_id: Mapped[UUID] = mapped_column(ForeignKey("units_of_measure.id", ondelete="RESTRICT"))
    position: Mapped[str] = mapped_column(String(100), default="", server_default="")
    sequence: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    required: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    notes: Mapped[str] = mapped_column(Text, default="", server_default="")


class BomApprovedAlternative(Identity, Base):
    __tablename__ = "bom_approved_alternatives"
    __table_args__ = (
        UniqueConstraint("bom_item_id", "component_id", name="uq_bom_alternatives_item_component"),
    )

    bom_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("product_revision_bom_items.id", ondelete="CASCADE")
    )
    component_id: Mapped[UUID] = mapped_column(ForeignKey("components.id", ondelete="RESTRICT"))
    notes: Mapped[str] = mapped_column(Text, default="", server_default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProductRevisionDocument(Identity, Base):
    __tablename__ = "product_revision_documents"
    __table_args__ = (
        UniqueConstraint("revision_id", "attachment_id", name="uq_revision_documents_attachment"),
        CheckConstraint(
            "document_type IN ('USER_MANUAL','MANUFACTURING','CONFIGURATION','DRAWING',"
            "'WIRING_DIAGRAM','OTHER')",
            name="document_type",
        ),
    )

    revision_id: Mapped[UUID] = mapped_column(
        ForeignKey("product_revisions.id", ondelete="CASCADE"), index=True
    )
    attachment_id: Mapped[UUID] = mapped_column(
        ForeignKey("attachments.id", ondelete="RESTRICT"), unique=True
    )
    document_type: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(255))
    sequence: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
