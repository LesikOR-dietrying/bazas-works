"""Expand projects with R&D branches and generic configurations."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008_rnd_evolution"
down_revision = "0007_identity_roles_username"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("goal", sa.Text(), server_default="", nullable=False))
    op.add_column("projects", sa.Column("start_date", sa.Date(), nullable=True))
    op.add_column("projects", sa.Column("deadline", sa.Date(), nullable=True))
    op.create_check_constraint(
        op.f("ck_projects_date_order"),
        "projects",
        "start_date IS NULL OR deadline IS NULL OR deadline >= start_date",
    )
    op.add_column(
        "setups",
        sa.Column(
            "attributes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )

    op.create_table(
        "rd_branches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("purpose", sa.Text(), server_default="", nullable=False),
        sa.Column("status", sa.String(20), server_default="OPEN", nullable=False),
        sa.Column("responsible_user_id", sa.Uuid(), nullable=False),
        sa.Column("change_summary", sa.Text(), server_default="", nullable=False),
        sa.Column("result_summary", sa.Text(), server_default="", nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_rd_branches"),
        sa.UniqueConstraint("project_id", "id", name="uq_rd_branches_project_id_pair"),
        sa.UniqueConstraint("project_id", "name", name="uq_rd_branches_project_name"),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_rd_branches_project_id_projects",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["rd_branches.id"],
            name="fk_rd_branches_parent_id_rd_branches",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["responsible_user_id"],
            ["users.id"],
            name="fk_rd_branches_responsible_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
            name="fk_rd_branches_created_by_id_users",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("length(trim(name)) > 0", name=op.f("ck_rd_branches_name_nonempty")),
        sa.CheckConstraint(
            "status IN ('OPEN','IN_REVIEW','APPROVED','REJECTED','CLOSED')",
            name=op.f("ck_rd_branches_status"),
        ),
        sa.CheckConstraint(
            "parent_id IS NULL OR parent_id <> id", name=op.f("ck_rd_branches_parent_not_self")
        ),
        sa.CheckConstraint(
            "(status = 'CLOSED') = (closed_at IS NOT NULL)",
            name=op.f("ck_rd_branches_closed_state"),
        ),
    )
    for column in ("project_id", "parent_id", "responsible_user_id", "created_by_id", "status"):
        op.create_index(f"ix_rd_branches_{column}", "rd_branches", [column])

    op.create_table(
        "branch_configurations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("branch_id", sa.Uuid(), nullable=False),
        sa.Column("setup_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_branch_configurations"),
        sa.UniqueConstraint("branch_id", "setup_id", name="uq_branch_configurations_branch_setup"),
        sa.ForeignKeyConstraint(
            ["branch_id"],
            ["rd_branches.id"],
            name="fk_branch_configurations_branch_id_rd_branches",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["setup_id"],
            ["setups.id"],
            name="fk_branch_configurations_setup_id_setups",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
            name="fk_branch_configurations_created_by_id_users",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "role IN ('BASELINE','CANDIDATE')", name=op.f("ck_branch_configurations_role")
        ),
    )
    op.create_index("ix_branch_configurations_branch_id", "branch_configurations", ["branch_id"])
    op.create_index("ix_branch_configurations_setup_id", "branch_configurations", ["setup_id"])
    op.create_index(
        "uq_branch_configurations_one_baseline",
        "branch_configurations",
        ["branch_id"],
        unique=True,
        postgresql_where=sa.text("role = 'BASELINE'"),
    )

    op.create_table(
        "rnd_promotion_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("branch_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_setup_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(20), server_default="REQUESTED", nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("requested_by_id", sa.Uuid(), nullable=False),
        sa.Column("reviewed_by_id", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_rnd_promotion_requests"),
        sa.ForeignKeyConstraint(
            ["branch_id"],
            ["rd_branches.id"],
            name="fk_rnd_promotion_requests_branch_id_rd_branches",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["candidate_setup_id"],
            ["setups.id"],
            name="fk_rnd_promotion_requests_candidate_setup_id_setups",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by_id"],
            ["users.id"],
            name="fk_rnd_promotion_requests_requested_by_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_id"],
            ["users.id"],
            name="fk_rnd_promotion_requests_reviewed_by_id_users",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "status IN ('REQUESTED','APPROVED','REJECTED')",
            name=op.f("ck_rnd_promotion_requests_status"),
        ),
        sa.CheckConstraint(
            "length(trim(reason)) > 0", name=op.f("ck_rnd_promotion_requests_reason_nonempty")
        ),
        sa.CheckConstraint(
            "(status = 'REQUESTED' AND reviewed_by_id IS NULL AND reviewed_at IS NULL) OR "
            "(status IN ('APPROVED','REJECTED') AND reviewed_by_id IS NOT NULL "
            "AND reviewed_at IS NOT NULL)",
            name=op.f("ck_rnd_promotion_requests_review_state"),
        ),
    )
    for column in ("branch_id", "candidate_setup_id", "status"):
        op.create_index(f"ix_rnd_promotion_requests_{column}", "rnd_promotion_requests", [column])

    op.add_column("tasks", sa.Column("branch_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_tasks_project_branch_rd_branches",
        "tasks",
        "rd_branches",
        ["project_id", "branch_id"],
        ["project_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_tasks_branch_id", "tasks", ["branch_id"])

    op.add_column("tests", sa.Column("branch_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_tests_project_branch_rd_branches",
        "tests",
        "rd_branches",
        ["project_id", "branch_id"],
        ["project_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        op.f("ck_tests_branch_requires_project"),
        "tests",
        "branch_id IS NULL OR project_id IS NOT NULL",
    )
    op.create_index("ix_tests_branch_id", "tests", ["branch_id"])

    op.add_column("attachments", sa.Column("branch_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_attachments_branch_id_rd_branches",
        "attachments",
        "rd_branches",
        ["branch_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_attachments_branch_id", "attachments", ["branch_id"])
    op.drop_constraint(op.f("ck_attachments_one_owner"), "attachments", type_="check")
    op.create_check_constraint(
        op.f("ck_attachments_one_owner"),
        "attachments",
        "num_nonnulls(project_id, task_id, setup_id, component_id, test_id, "
        "firmware_revision_id, branch_id) = 1",
    )

    op.add_column("comments", sa.Column("branch_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_comments_branch_id_rd_branches",
        "comments",
        "rd_branches",
        ["branch_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_comments_branch_id", "comments", ["branch_id"])
    op.drop_constraint(op.f("ck_comments_one_owner"), "comments", type_="check")
    op.create_check_constraint(
        op.f("ck_comments_one_owner"),
        "comments",
        "num_nonnulls(project_id, task_id, setup_id, test_id, branch_id) = 1",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_comments_one_owner"), "comments", type_="check")
    op.create_check_constraint(
        op.f("ck_comments_one_owner"),
        "comments",
        "num_nonnulls(project_id, task_id, setup_id, test_id) = 1",
    )
    op.drop_index("ix_comments_branch_id", table_name="comments")
    op.drop_constraint("fk_comments_branch_id_rd_branches", "comments", type_="foreignkey")
    op.drop_column("comments", "branch_id")
    op.drop_constraint(op.f("ck_attachments_one_owner"), "attachments", type_="check")
    op.create_check_constraint(
        op.f("ck_attachments_one_owner"),
        "attachments",
        "num_nonnulls(project_id, task_id, setup_id, component_id, test_id, "
        "firmware_revision_id) = 1",
    )
    op.drop_index("ix_attachments_branch_id", table_name="attachments")
    op.drop_constraint("fk_attachments_branch_id_rd_branches", "attachments", type_="foreignkey")
    op.drop_column("attachments", "branch_id")
    op.drop_index("ix_tests_branch_id", table_name="tests")
    op.drop_constraint(op.f("ck_tests_branch_requires_project"), "tests", type_="check")
    op.drop_constraint("fk_tests_project_branch_rd_branches", "tests", type_="foreignkey")
    op.drop_column("tests", "branch_id")
    op.drop_index("ix_tasks_branch_id", table_name="tasks")
    op.drop_constraint("fk_tasks_project_branch_rd_branches", "tasks", type_="foreignkey")
    op.drop_column("tasks", "branch_id")
    op.drop_table("rnd_promotion_requests")
    op.drop_table("branch_configurations")
    op.drop_table("rd_branches")
    op.drop_column("setups", "attributes")
    op.drop_constraint(op.f("ck_projects_date_order"), "projects", type_="check")
    op.drop_column("projects", "deadline")
    op.drop_column("projects", "start_date")
    op.drop_column("projects", "goal")
