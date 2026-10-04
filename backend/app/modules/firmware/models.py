from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import Identity, Timestamps


class FirmwareRevision(Identity, Base):
    __tablename__ = "firmware_revisions"
    __table_args__ = (
        UniqueConstraint("setup_id", "version_name", name="uq_firmware_revisions_setup_version"),
        UniqueConstraint("setup_id", "id", name="uq_firmware_revisions_setup_id_pair"),
        CheckConstraint("length(trim(version_name)) > 0", name="version_name_nonempty"),
        CheckConstraint("length(trim(firmware_type)) > 0", name="firmware_type_nonempty"),
        CheckConstraint("length(trim(firmware_version)) > 0", name="firmware_version_nonempty"),
    )
    setup_id: Mapped[UUID] = mapped_column(ForeignKey("setups.id", ondelete="RESTRICT"))
    version_name: Mapped[str] = mapped_column(String(255))
    firmware_type: Mapped[str] = mapped_column(String(255))
    firmware_version: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    config_text: Mapped[str] = mapped_column(Text, default="", server_default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )


class FirmwareArtifact(Identity, Timestamps, Base):
    __tablename__ = "firmware_artifacts"
    __table_args__ = (
        UniqueConstraint("name", name="uq_firmware_artifacts_name"),
        CheckConstraint("length(trim(name)) > 0", name="name_nonempty"),
    )

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="", server_default="")


class FirmwareRelease(Identity, Base):
    __tablename__ = "firmware_releases"
    __table_args__ = (
        UniqueConstraint("artifact_id", "version", name="uq_firmware_releases_artifact_version"),
        CheckConstraint("length(trim(version)) > 0", name="version_nonempty"),
    )

    artifact_id: Mapped[UUID] = mapped_column(
        ForeignKey("firmware_artifacts.id", ondelete="RESTRICT"), index=True
    )
    version: Mapped[str] = mapped_column(String(255))
    firmware_type: Mapped[str] = mapped_column(String(255), default="", server_default="")
    upstream_version: Mapped[str] = mapped_column(String(255), default="", server_default="")
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    config_text: Mapped[str] = mapped_column(Text, default="", server_default="")
    checksum: Mapped[str] = mapped_column(String(128), default="", server_default="")
    binary_attachment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "attachments.id",
            ondelete="RESTRICT",
            use_alter=True,
            name="fk_firmware_releases_binary_attachment_id_attachments",
        )
    )
    config_attachment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "attachments.id",
            ondelete="RESTRICT",
            use_alter=True,
            name="fk_firmware_releases_config_attachment_id_attachments",
        )
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )


class FirmwareRequirement(Identity, Timestamps, Base):
    __tablename__ = "firmware_requirements"
    __table_args__ = (
        UniqueConstraint("revision_id", "release_id", "purpose", name="uq_firmware_requirements"),
        CheckConstraint("length(trim(purpose)) > 0", name="purpose_nonempty"),
        CheckConstraint("jsonb_typeof(configuration) = 'object'", name="configuration_object"),
    )

    revision_id: Mapped[UUID] = mapped_column(
        ForeignKey("product_revisions.id", ondelete="CASCADE"), index=True
    )
    release_id: Mapped[UUID] = mapped_column(
        ForeignKey("firmware_releases.id", ondelete="RESTRICT"), index=True
    )
    purpose: Mapped[str] = mapped_column(String(255))
    notes: Mapped[str] = mapped_column(Text, default="", server_default="")
    configuration: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )
