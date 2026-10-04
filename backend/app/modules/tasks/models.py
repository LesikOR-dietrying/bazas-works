from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.models import Identity, Timestamps
from app.modules.projects.models import Project
from app.modules.users.models import User


class TaskStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    TESTING = "TESTING"
    DONE = "DONE"


class Priority(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Task(Identity, Timestamps, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "status IN ('TODO','IN_PROGRESS','BLOCKED','TESTING','DONE')", name="status"
        ),
        CheckConstraint("priority IN ('LOW','NORMAL','HIGH','CRITICAL')", name="priority"),
        CheckConstraint("length(trim(title)) > 0", name="title_nonempty"),
        CheckConstraint("(status = 'DONE') = (completed_at IS NOT NULL)", name="completion"),
        Index("ix_tasks_assignee_status_deadline", "assignee_id", "status", "deadline"),
        Index("ix_tasks_project_status", "project_id", "status"),
        ForeignKeyConstraint(
            ["project_id", "branch_id"],
            ["rd_branches.project_id", "rd_branches.id"],
            name="fk_tasks_project_branch_rd_branches",
            ondelete="RESTRICT",
        ),
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="RESTRICT"))
    branch_id: Mapped[UUID | None] = mapped_column(index=True)
    assignee_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), default=TaskStatus.TODO)
    priority: Mapped[str] = mapped_column(String(20), default=Priority.NORMAL, index=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    result: Mapped[str] = mapped_column(Text, default="", server_default="")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    project: Mapped[Project] = relationship(lazy="joined")
    assignee: Mapped[User | None] = relationship(foreign_keys=[assignee_id], lazy="joined")
    creator: Mapped[User] = relationship(foreign_keys=[created_by_id], lazy="joined")

    @property
    def project_name(self) -> str:
        return self.project.name

    @property
    def assignee_name(self) -> str | None:
        return self.assignee.full_name if self.assignee else None

    @property
    def created_by_name(self) -> str:
        return self.creator.full_name
