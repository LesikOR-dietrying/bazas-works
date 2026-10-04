"""Authorized attachments and comments."""

import sqlalchemy as sa
from alembic import op

revision = "0006_files_comments"
down_revision = "0005_tests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "attachments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("stored_filename", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(255), nullable=False),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("uploaded_by_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("task_id", sa.Uuid(), nullable=True),
        sa.Column("setup_id", sa.Uuid(), nullable=True),
        sa.Column("component_id", sa.Uuid(), nullable=True),
        sa.Column("test_id", sa.Uuid(), nullable=True),
        sa.Column("firmware_revision_id", sa.Uuid(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_attachments"),
        sa.UniqueConstraint("storage_path", name="uq_attachments_storage_path"),
        sa.ForeignKeyConstraint(
            ["uploaded_by_id"],
            ["users.id"],
            name="fk_attachments_uploaded_by_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_attachments_project_id_projects",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"], ["tasks.id"], name="fk_attachments_task_id_tasks", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["setup_id"], ["setups.id"], name="fk_attachments_setup_id_setups", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["component_id"],
            ["components.id"],
            name="fk_attachments_component_id_components",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["test_id"], ["tests.id"], name="fk_attachments_test_id_tests", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["firmware_revision_id"],
            ["firmware_revisions.id"],
            name="fk_attachments_firmware_revision_id_firmware_revisions",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("size >= 0", name=op.f("ck_attachments_size_nonnegative")),
        sa.CheckConstraint(
            "num_nonnulls(project_id, task_id, setup_id, component_id, test_id, "
            "firmware_revision_id) = 1",
            name=op.f("ck_attachments_one_owner"),
        ),
    )
    for column in (
        "uploaded_by_id",
        "project_id",
        "task_id",
        "setup_id",
        "component_id",
        "test_id",
        "firmware_revision_id",
    ):
        op.create_index(f"ix_attachments_{column}", "attachments", [column])

    op.create_table(
        "comments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("task_id", sa.Uuid(), nullable=True),
        sa.Column("setup_id", sa.Uuid(), nullable=True),
        sa.Column("test_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_comments"),
        sa.ForeignKeyConstraint(
            ["author_id"], ["users.id"], name="fk_comments_author_id_users", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_comments_project_id_projects",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"], ["tasks.id"], name="fk_comments_task_id_tasks", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["setup_id"], ["setups.id"], name="fk_comments_setup_id_setups", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["test_id"], ["tests.id"], name="fk_comments_test_id_tests", ondelete="RESTRICT"
        ),
        sa.CheckConstraint("length(trim(text)) > 0", name=op.f("ck_comments_text_nonempty")),
        sa.CheckConstraint(
            "num_nonnulls(project_id, task_id, setup_id, test_id) = 1",
            name=op.f("ck_comments_one_owner"),
        ),
    )
    for column in ("author_id", "project_id", "task_id", "setup_id", "test_id"):
        op.create_index(f"ix_comments_{column}", "comments", [column])


def downgrade() -> None:
    op.drop_table("comments")
    op.drop_table("attachments")
