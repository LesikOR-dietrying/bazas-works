from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.models import Identity
from app.modules.users.models import User


class Attachment(Identity, Base):
    __tablename__ = "attachments"
    __table_args__ = (
        CheckConstraint("size >= 0", name="size_nonnegative"),
        CheckConstraint(
            "num_nonnulls(project_id, task_id, setup_id, component_id, test_id, "
            "firmware_revision_id, branch_id, product_id, product_revision_id, "
            "firmware_release_id, stage_execution_id) = 1",
            name="one_owner",
        ),
    )

    original_filename: Mapped[str] = mapped_column(Text)
    stored_filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(255))
    size: Mapped[int] = mapped_column(BigInteger)
    storage_path: Mapped[str] = mapped_column(Text, unique=True)
    uploaded_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), index=True
    )
    task_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="RESTRICT"), index=True
    )
    setup_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("setups.id", ondelete="RESTRICT"), index=True
    )
    component_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("components.id", ondelete="RESTRICT"), index=True
    )
    test_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("tests.id", ondelete="RESTRICT"), index=True
    )
    firmware_revision_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("firmware_revisions.id", ondelete="RESTRICT"), index=True
    )
    branch_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("rd_branches.id", ondelete="RESTRICT"), index=True
    )
    product_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), index=True
    )
    product_revision_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("product_revisions.id", ondelete="RESTRICT"), index=True
    )
    firmware_release_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("firmware_releases.id", ondelete="RESTRICT"), index=True
    )
    stage_execution_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("stage_executions.id", ondelete="RESTRICT", use_alter=True), index=True
    )
    uploaded_by: Mapped[User] = relationship(lazy="joined")

    @property
    def uploaded_by_name(self) -> str:
        return self.uploaded_by.full_name
