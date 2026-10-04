from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.models import Identity, Timestamps
from app.modules.users.models import User


class Comment(Identity, Timestamps, Base):
    __tablename__ = "comments"
    __table_args__ = (
        CheckConstraint("length(trim(text)) > 0", name="text_nonempty"),
        CheckConstraint(
            "num_nonnulls(project_id, task_id, setup_id, test_id, branch_id) = 1",
            name="one_owner",
        ),
    )

    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    text: Mapped[str] = mapped_column(Text)
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), index=True
    )
    task_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="RESTRICT"), index=True
    )
    setup_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("setups.id", ondelete="RESTRICT"), index=True
    )
    test_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("tests.id", ondelete="RESTRICT"), index=True
    )
    branch_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("rd_branches.id", ondelete="RESTRICT"), index=True
    )
    author: Mapped[User] = relationship(lazy="joined")

    @property
    def author_name(self) -> str:
        return self.author.full_name
