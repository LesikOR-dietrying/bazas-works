"""Universal tests, equipment and numeric measurements."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0005_tests"
down_revision = "0004_components_setups_firmware"
branch_labels = None
depends_on = None

MEASUREMENT_FIELDS = (
    "throttle_percent",
    "voltage_v",
    "current_a",
    "power_w",
    "rpm",
    "thrust_kg",
    "efficiency_g_w",
    "motor_temperature_c",
    "esc_temperature_c",
    "timestamp_seconds",
)
NONNEGATIVE_FIELDS = (
    "voltage_v",
    "current_a",
    "power_w",
    "rpm",
    "thrust_kg",
    "efficiency_g_w",
    "timestamp_seconds",
)
TEMPERATURE_FIELDS = ("motor_temperature_c", "esc_temperature_c")


def timestamps() -> list[sa.Column]:
    return [
        sa.Column(name, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
        for name in ("created_at", "updated_at")
    ]


def upgrade() -> None:
    op.create_table(
        "tests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("test_type", sa.String(32), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("setup_id", sa.Uuid(), nullable=True),
        sa.Column("component_id", sa.Uuid(), nullable=True),
        sa.Column("firmware_revision_id", sa.Uuid(), nullable=True),
        sa.Column("performed_by_id", sa.Uuid(), nullable=True),
        sa.Column("test_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("conditions", JSONB(), server_default="{}", nullable=False),
        sa.Column("result_summary", JSONB(), server_default="{}", nullable=False),
        sa.Column("conclusion", sa.Text(), server_default="", nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_tests"),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_tests_project_id_projects",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["setup_id"], ["setups.id"], name="fk_tests_setup_id_setups", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["component_id"],
            ["components.id"],
            name="fk_tests_component_id_components",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["firmware_revision_id"],
            ["firmware_revisions.id"],
            name="fk_tests_firmware_revision_id_firmware_revisions",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["performed_by_id"],
            ["users.id"],
            name="fk_tests_performed_by_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id", "setup_id"],
            ["project_setups.project_id", "project_setups.setup_id"],
            name="fk_tests_project_setup_project_setups",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["setup_id", "firmware_revision_id"],
            ["firmware_revisions.setup_id", "firmware_revisions.id"],
            name="fk_tests_setup_firmware_firmware_revisions",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("length(trim(name)) > 0", name=op.f("ck_tests_name_nonempty")),
        sa.CheckConstraint(
            "test_type IN ('MOTOR_BENCH','ESC_BENCH','BATTERY','PROPELLER','FLIGHT',"
            "'ENDURANCE','RANGE','TEMPERATURE','FRAME','ANTENNA','OTHER')",
            name=op.f("ck_tests_test_type"),
        ),
        sa.CheckConstraint(
            "status IN ('PLANNED','IN_PROGRESS','PASS','FAIL','PARTIAL')",
            name=op.f("ck_tests_status"),
        ),
        sa.CheckConstraint(
            "project_id IS NOT NULL OR setup_id IS NOT NULL OR component_id IS NOT NULL",
            name=op.f("ck_tests_has_subject"),
        ),
        sa.CheckConstraint(
            "firmware_revision_id IS NULL OR setup_id IS NOT NULL",
            name=op.f("ck_tests_firmware_needs_setup"),
        ),
        sa.CheckConstraint(
            "test_type NOT IN ('FLIGHT','ENDURANCE') OR setup_id IS NOT NULL",
            name=op.f("ck_tests_flight_needs_setup"),
        ),
        sa.CheckConstraint(
            "test_type != 'MOTOR_BENCH' OR component_id IS NOT NULL",
            name=op.f("ck_tests_motor_needs_component"),
        ),
        sa.CheckConstraint(
            "status = 'PLANNED' OR (performed_by_id IS NOT NULL AND test_date IS NOT NULL)",
            name=op.f("ck_tests_performed_when_executed"),
        ),
        sa.CheckConstraint(
            "jsonb_typeof(conditions) = 'object'", name=op.f("ck_tests_conditions_object")
        ),
        sa.CheckConstraint(
            "jsonb_typeof(result_summary) = 'object'",
            name=op.f("ck_tests_result_summary_object"),
        ),
    )
    for name, columns in {
        "ix_tests_project_id": ["project_id"],
        "ix_tests_firmware_revision_id": ["firmware_revision_id"],
        "ix_tests_performed_by_id": ["performed_by_id"],
        "ix_tests_test_type_test_date": ["test_type", "test_date"],
        "ix_tests_status_test_date": ["status", "test_date"],
        "ix_tests_setup_test_date": ["setup_id", "test_date"],
        "ix_tests_component_test_date": ["component_id", "test_date"],
    }.items():
        op.create_index(name, "tests", columns)

    op.create_table(
        "test_components",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("test_id", sa.Uuid(), nullable=False),
        sa.Column("component_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("notes", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_test_components"),
        sa.UniqueConstraint(
            "test_id", "component_id", "role", name="uq_test_components_test_component_role"
        ),
        sa.ForeignKeyConstraint(
            ["test_id"], ["tests.id"], name="fk_test_components_test_id_tests", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["component_id"],
            ["components.id"],
            name="fk_test_components_component_id_components",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "role IN ('ESC','PROPELLER','BATTERY','OTHER')", name=op.f("ck_test_components_role")
        ),
    )
    op.create_index("ix_test_components_component_id", "test_components", ["component_id"])

    numeric_columns = [
        sa.Column(name, sa.Numeric(14, 4), nullable=True) for name in MEASUREMENT_FIELDS
    ]
    nonnegative_checks = [
        sa.CheckConstraint(
            f"{name} IS NULL OR ({name} >= 0 AND "
            f"{name}::text NOT IN ('NaN','Infinity','-Infinity'))",
            name=op.f(f"ck_test_measurements_{name}_nonnegative"),
        )
        for name in NONNEGATIVE_FIELDS
    ]
    temperature_checks = [
        sa.CheckConstraint(
            f"{name} IS NULL OR {name}::text NOT IN ('NaN','Infinity','-Infinity')",
            name=op.f(f"ck_test_measurements_{name}_finite"),
        )
        for name in TEMPERATURE_FIELDS
    ]
    op.create_table(
        "test_measurements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("test_id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        *numeric_columns,
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_test_measurements"),
        sa.UniqueConstraint("test_id", "sequence", name="uq_test_measurements_test_sequence"),
        sa.ForeignKeyConstraint(
            ["test_id"], ["tests.id"], name="fk_test_measurements_test_id_tests", ondelete="CASCADE"
        ),
        sa.CheckConstraint("sequence >= 0", name=op.f("ck_test_measurements_sequence_nonnegative")),
        sa.CheckConstraint(
            "throttle_percent IS NULL OR (throttle_percent BETWEEN 0 AND 100 "
            "AND throttle_percent::text NOT IN ('NaN','Infinity','-Infinity'))",
            name=op.f("ck_test_measurements_throttle_range"),
        ),
        *nonnegative_checks,
        *temperature_checks,
    )


def downgrade() -> None:
    op.drop_table("test_measurements")
    op.drop_table("test_components")
    op.drop_table("tests")
