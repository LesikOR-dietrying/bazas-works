"""Add username identity and additive many-to-many roles."""

from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision = "0007_identity_roles_username"
down_revision = "0006_files_comments"
branch_labels = None
depends_on = None


ROLE_IDS = {
    "ADMINISTRATOR": UUID("00000000-0000-4000-8000-000000000001"),
    "ENGINEER": UUID("00000000-0000-4000-8000-000000000002"),
    "RND_ENGINEER": UUID("00000000-0000-4000-8000-000000000003"),
    "PRODUCTION_MANAGER": UUID("00000000-0000-4000-8000-000000000004"),
    "PROCUREMENT_SPECIALIST": UUID("00000000-0000-4000-8000-000000000005"),
    "ASSEMBLER": UUID("00000000-0000-4000-8000-000000000006"),
    "ELECTRONICS_TECHNICIAN": UUID("00000000-0000-4000-8000-000000000007"),
    "FIRMWARE_ENGINEER": UUID("00000000-0000-4000-8000-000000000008"),
    "TEST_PILOT": UUID("00000000-0000-4000-8000-000000000009"),
    "TEST_ENGINEER": UUID("00000000-0000-4000-8000-000000000010"),
    "QUALITY_CONTROLLER": UUID("00000000-0000-4000-8000-000000000011"),
}


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(320), nullable=True))
    op.execute("UPDATE users SET username = lower(trim(email))")
    op.alter_column("users", "username", existing_type=sa.String(320), nullable=False)
    op.create_check_constraint(
        op.f("ck_users_username_nonempty"), "users", "length(trim(username)) > 0"
    )
    op.create_index("uq_users_username_lower", "users", [sa.text("lower(username)")], unique=True)
    op.alter_column("users", "email", existing_type=sa.String(320), nullable=True)

    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_roles"),
        sa.UniqueConstraint("code", name="uq_roles_code"),
        sa.CheckConstraint("length(trim(code)) > 0", name=op.f("ck_roles_code_nonempty")),
        sa.CheckConstraint("length(trim(name)) > 0", name=op.f("ck_roles_name_nonempty")),
    )
    op.create_table(
        "user_roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("assigned_by_id", sa.Uuid(), nullable=True),
        sa.Column(
            "assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user_roles"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_user_roles_user_id_users", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.id"], name="fk_user_roles_role_id_roles", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["assigned_by_id"],
            ["users.id"],
            name="fk_user_roles_assigned_by_id_users",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_id_role_id"),
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])

    roles = sa.table(
        "roles",
        sa.column("id", sa.Uuid()),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("is_active", sa.Boolean()),
    )
    names = {
        "ADMINISTRATOR": "Administrator",
        "ENGINEER": "Engineer",
        "RND_ENGINEER": "R&D Engineer",
        "PRODUCTION_MANAGER": "Production Manager",
        "PROCUREMENT_SPECIALIST": "Procurement Specialist",
        "ASSEMBLER": "Assembler",
        "ELECTRONICS_TECHNICIAN": "Electronics Technician",
        "FIRMWARE_ENGINEER": "Firmware Engineer",
        "TEST_PILOT": "Test Pilot",
        "TEST_ENGINEER": "Test Engineer",
        "QUALITY_CONTROLLER": "Quality Controller",
    }
    op.bulk_insert(
        roles,
        [
            {"id": identifier, "code": code, "name": names[code], "is_active": True}
            for code, identifier in ROLE_IDS.items()
        ],
    )
    mapping = {
        "ADMIN": ("ADMINISTRATOR",),
        "MANAGER": ("PRODUCTION_MANAGER",),
        "ENGINEER": ("ENGINEER", "RND_ENGINEER"),
        "EMPLOYEE": (),
    }
    for legacy_role, role_codes in mapping.items():
        for role_code in role_codes:
            op.execute(
                sa.text(
                    "INSERT INTO user_roles (id, user_id, role_id) "
                    "SELECT CAST(md5(CAST(id AS text) || :suffix) AS uuid), id, "
                    "CAST(:role_id AS uuid) "
                    "FROM users WHERE role = :legacy_role"
                ).bindparams(
                    suffix=f":{role_code}",
                    role_id=str(ROLE_IDS[role_code]),
                    legacy_role=legacy_role,
                )
            )


def downgrade() -> None:
    op.drop_table("user_roles")
    op.drop_table("roles")
    op.execute("UPDATE users SET email = username || '@legacy.invalid' WHERE email IS NULL")
    op.alter_column("users", "email", existing_type=sa.String(320), nullable=False)
    op.drop_index("uq_users_username_lower", table_name="users")
    op.drop_constraint(op.f("ck_users_username_nonempty"), "users", type_="check")
    op.drop_column("users", "username")
