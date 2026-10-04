from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.models import Identity, Timestamps
from app.modules.projects.models import Project
from app.modules.setups.models import Setup
from app.modules.users.models import User


class BranchStatus(StrEnum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"


class ConfigurationRole(StrEnum):
    BASELINE = "BASELINE"
    CANDIDATE = "CANDIDATE"


class PromotionRequestStatus(StrEnum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class RDBranch(Identity, Timestamps, Base):
    __tablename__ = "rd_branches"
    __table_args__ = (
        UniqueConstraint("project_id", "id", name="uq_rd_branches_project_id_pair"),
        UniqueConstraint("project_id", "name", name="uq_rd_branches_project_name"),
        CheckConstraint("length(trim(name)) > 0", name="name_nonempty"),
        CheckConstraint(
            "status IN ('OPEN','IN_REVIEW','APPROVED','REJECTED','CLOSED')", name="status"
        ),
        CheckConstraint("parent_id IS NULL OR parent_id <> id", name="parent_not_self"),
        CheckConstraint("(status = 'CLOSED') = (closed_at IS NOT NULL)", name="closed_state"),
    )
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), index=True
    )
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("rd_branches.id", ondelete="RESTRICT"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    purpose: Mapped[str] = mapped_column(Text, default="", server_default="")
    status: Mapped[str] = mapped_column(String(20), default=BranchStatus.OPEN, index=True)
    responsible_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    change_summary: Mapped[str] = mapped_column(Text, default="", server_default="")
    result_summary: Mapped[str] = mapped_column(Text, default="", server_default="")
    created_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    project: Mapped[Project] = relationship(lazy="joined")
    responsible: Mapped[User] = relationship(foreign_keys=[responsible_user_id], lazy="joined")
    creator: Mapped[User] = relationship(foreign_keys=[created_by_id], lazy="joined")
    parent: Mapped[RDBranch | None] = relationship(remote_side="RDBranch.id", lazy="joined")

    @property
    def responsible_name(self) -> str:
        return self.responsible.full_name

    @property
    def parent_name(self) -> str | None:
        return self.parent.name if self.parent else None


class BranchConfiguration(Identity, Base):
    __tablename__ = "branch_configurations"
    __table_args__ = (
        UniqueConstraint("branch_id", "setup_id", name="uq_branch_configurations_branch_setup"),
        CheckConstraint("role IN ('BASELINE','CANDIDATE')", name="role"),
        Index(
            "uq_branch_configurations_one_baseline",
            "branch_id",
            unique=True,
            postgresql_where=text("role = 'BASELINE'"),
        ),
    )
    branch_id: Mapped[UUID] = mapped_column(
        ForeignKey("rd_branches.id", ondelete="CASCADE"), index=True
    )
    setup_id: Mapped[UUID] = mapped_column(ForeignKey("setups.id", ondelete="RESTRICT"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    created_by_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    setup: Mapped[Setup] = relationship(lazy="joined")


class RNDPromotionRequest(Identity, Base):
    __tablename__ = "rnd_promotion_requests"
    __table_args__ = (
        CheckConstraint("status IN ('REQUESTED','APPROVED','REJECTED')", name="status"),
        CheckConstraint("length(trim(reason)) > 0", name="reason_nonempty"),
        CheckConstraint(
            "(status = 'REQUESTED' AND reviewed_by_id IS NULL AND reviewed_at IS NULL) OR "
            "(status IN ('APPROVED','REJECTED') AND reviewed_by_id IS NOT NULL "
            "AND reviewed_at IS NOT NULL)",
            name="review_state",
        ),
    )
    branch_id: Mapped[UUID] = mapped_column(
        ForeignKey("rd_branches.id", ondelete="RESTRICT"), index=True
    )
    candidate_setup_id: Mapped[UUID] = mapped_column(
        ForeignKey("setups.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default=PromotionRequestStatus.REQUESTED, index=True
    )
    reason: Mapped[str] = mapped_column(Text)
    requested_by_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    reviewed_by_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_notes: Mapped[str] = mapped_column(Text, default="", server_default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    candidate: Mapped[Setup] = relationship(lazy="joined")
    requester: Mapped[User] = relationship(foreign_keys=[requested_by_id], lazy="joined")
    reviewer: Mapped[User | None] = relationship(foreign_keys=[reviewed_by_id], lazy="joined")

    @property
    def candidate_name(self) -> str:
        return f"{self.candidate.name} · {self.candidate.version}"

    @property
    def requested_by_name(self) -> str:
        return self.requester.full_name

    @property
    def reviewed_by_name(self) -> str | None:
        return self.reviewer.full_name if self.reviewer else None
