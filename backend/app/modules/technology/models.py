from enum import StrEnum
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import Identity, Timestamps


class ContentBlockType(StrEnum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    CHECKLIST = "CHECKLIST"
    WARNING = "WARNING"
    FILE = "FILE"
    ANNOTATED_IMAGE = "ANNOTATED_IMAGE"
    MEASUREMENT = "MEASUREMENT"
    VIDEO = "VIDEO"


class TechnologyCard(Identity, Timestamps, Base):
    __tablename__ = "technology_cards"
    __table_args__ = (UniqueConstraint("revision_id", name="uq_technology_cards_revision"),)

    revision_id: Mapped[UUID] = mapped_column(
        ForeignKey("product_revisions.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="", server_default="")


class TechnologyOperation(Identity, Timestamps, Base):
    __tablename__ = "technology_operations"
    __table_args__ = (
        UniqueConstraint("card_id", "sequence", name="uq_technology_operations_sequence"),
        CheckConstraint("sequence >= 0", name="sequence_nonnegative"),
        CheckConstraint("length(trim(name)) > 0", name="name_nonempty"),
    )

    card_id: Mapped[UUID] = mapped_column(
        ForeignKey("technology_cards.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    sequence: Mapped[int] = mapped_column(Integer)
    expected_result: Mapped[str] = mapped_column(Text, default="", server_default="")
    acceptance_criteria: Mapped[str] = mapped_column(Text, default="", server_default="")


class TechnologyContentBlock(Identity, Timestamps, Base):
    __tablename__ = "technology_content_blocks"
    __table_args__ = (
        UniqueConstraint("operation_id", "sequence", name="uq_technology_blocks_sequence"),
        CheckConstraint("sequence >= 0", name="sequence_nonnegative"),
        CheckConstraint(
            "block_type IN ('TEXT','IMAGE','CHECKLIST','WARNING','FILE','ANNOTATED_IMAGE',"
            "'MEASUREMENT','VIDEO')",
            name="block_type",
        ),
        CheckConstraint("jsonb_typeof(payload) = 'object'", name="payload_object"),
        CheckConstraint("jsonb_typeof(annotation_source) = 'object'", name="annotation_object"),
    )

    operation_id: Mapped[UUID] = mapped_column(
        ForeignKey("technology_operations.id", ondelete="CASCADE"), index=True
    )
    block_type: Mapped[str] = mapped_column(String(30))
    sequence: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict, server_default="{}")
    attachment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("attachments.id", ondelete="RESTRICT")
    )
    annotation_source: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )
    annotation_version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")


class ChecklistTemplateItem(Identity, Timestamps, Base):
    __tablename__ = "checklist_template_items"
    __table_args__ = (
        UniqueConstraint("block_id", "sequence", name="uq_checklist_items_sequence"),
        CheckConstraint("sequence >= 0", name="sequence_nonnegative"),
        CheckConstraint("length(trim(text)) > 0", name="text_nonempty"),
    )

    block_id: Mapped[UUID] = mapped_column(
        ForeignKey("technology_content_blocks.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(Text)
    sequence: Mapped[int] = mapped_column(Integer)
    required: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    note_required: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    photo_required: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
