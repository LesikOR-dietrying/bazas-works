"""Projects, participants and tasks."""

import sqlalchemy as sa
from alembic import op

revision = "0003_projects_tasks"
down_revision = "0002_auth_users"
branch_labels = None
depends_on = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column(name, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
        for name in ("created_at", "updated_at")
    ]


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("responsible_user_id", sa.Uuid(), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_projects"),
        sa.ForeignKeyConstraint(
            ["responsible_user_id"],
            ["users.id"],
            name="fk_projects_responsible_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "status IN ('PLANNED','IN_PROGRESS','TESTING','COMPLETED','FROZEN')",
            name=op.f("ck_projects_status"),
        ),
        sa.CheckConstraint("length(trim(name)) > 0", name=op.f("ck_projects_name_nonempty")),
    )
    op.create_index("ix_projects_status", "projects", ["status"])
    op.create_index("ix_projects_responsible_user_id", "projects", ["responsible_user_id"])
    op.create_table(
        "project_members",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_project_members"),
        sa.UniqueConstraint("project_id", "user_id", name="uq_project_members_project_id"),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_project_members_project_id_projects",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_project_members_user_id_users", ondelete="RESTRICT"
        ),
    )
    op.create_index("ix_project_members_user_id", "project_members", ["user_id"])
    op.create_table(
        "tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("assignee_id", sa.Uuid(), nullable=True),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result", sa.Text(), server_default="", nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_tasks"),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_tasks_project_id_projects",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["assignee_id"], ["users.id"], name="fk_tasks_assignee_id_users", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
            name="fk_tasks_created_by_id_users",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "status IN ('TODO','IN_PROGRESS','BLOCKED','TESTING','DONE')",
            name=op.f("ck_tasks_status"),
        ),
        sa.CheckConstraint(
            "priority IN ('LOW','NORMAL','HIGH','CRITICAL')", name=op.f("ck_tasks_priority")
        ),
        sa.CheckConstraint("length(trim(title)) > 0", name=op.f("ck_tasks_title_nonempty")),
        sa.CheckConstraint(
            "(status = 'DONE') = (completed_at IS NOT NULL)", name=op.f("ck_tasks_completion")
        ),
    )
    for name, columns in {
        "ix_tasks_assignee_status_deadline": ["assignee_id", "status", "deadline"],
        "ix_tasks_project_status": ["project_id", "status"],
        "ix_tasks_created_by_id": ["created_by_id"],
        "ix_tasks_priority": ["priority"],
        "ix_tasks_completed_at": ["completed_at"],
    }.items():
        op.create_index(name, "tasks", columns)


def downgrade() -> None:
    op.drop_table("tasks")
    op.drop_table("project_members")
    op.drop_table("projects")
