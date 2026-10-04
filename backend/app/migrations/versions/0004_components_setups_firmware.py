"""Components, setups, BOM, project links and firmware revisions."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0004_components_setups_firmware"
down_revision = "0003_projects_tasks"
branch_labels = None
depends_on = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column(name, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
        for name in ("created_at", "updated_at")
    ]


def upgrade() -> None:
    op.create_table(
        "components",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("manufacturer", sa.String(255), server_default="", nullable=False),
        sa.Column("model", sa.String(255), server_default="", nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("specifications", JSONB(), server_default="{}", nullable=False),
        sa.Column("datasheet_url", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), server_default="", nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_components"),
        sa.CheckConstraint(
            "category IN ('MOTOR','ESC','FLIGHT_CONTROLLER','PROPELLER','BATTERY',"
            "'CAMERA','VTX','RX','GPS','ANTENNA','FRAME','POWER_MODULE','OTHER')",
            name=op.f("ck_components_category"),
        ),
        sa.CheckConstraint("length(trim(name)) > 0", name=op.f("ck_components_name_nonempty")),
        sa.CheckConstraint(
            "jsonb_typeof(specifications) = 'object'",
            name=op.f("ck_components_specifications_object"),
        ),
    )
    op.create_index("ix_components_category", "components", ["category"])
    op.create_index("ix_components_manufacturer_model", "components", ["manufacturer", "model"])

    op.create_table(
        "setups",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("drone_class", sa.String(255), nullable=False),
        sa.Column("version", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("weight_kg", sa.Numeric(14, 4), nullable=True),
        sa.Column("payload_kg", sa.Numeric(14, 4), nullable=True),
        sa.Column("battery_description", sa.Text(), server_default="", nullable=False),
        sa.Column("battery_voltage", sa.Numeric(14, 4), nullable=True),
        sa.Column("battery_capacity_ah", sa.Numeric(14, 4), nullable=True),
        sa.Column("propeller_description", sa.Text(), server_default="", nullable=False),
        sa.Column("flight_time_minutes", sa.Numeric(14, 4), nullable=True),
        sa.Column("average_current_a", sa.Numeric(14, 4), nullable=True),
        sa.Column("max_current_a", sa.Numeric(14, 4), nullable=True),
        sa.Column("firmware_type", sa.String(255), server_default="", nullable=False),
        sa.Column("firmware_version", sa.String(255), server_default="", nullable=False),
        sa.Column("notes", sa.Text(), server_default="", nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_setups"),
        sa.UniqueConstraint("name", "version", name="uq_setups_name_version"),
        sa.CheckConstraint(
            "status IN ('DEVELOPMENT','TESTING','READY','DEPRECATED')",
            name=op.f("ck_setups_status"),
        ),
        sa.CheckConstraint("length(trim(name)) > 0", name=op.f("ck_setups_name_nonempty")),
        sa.CheckConstraint("length(trim(version)) > 0", name=op.f("ck_setups_version_nonempty")),
        sa.CheckConstraint(
            "length(trim(drone_class)) > 0", name=op.f("ck_setups_drone_class_nonempty")
        ),
        sa.CheckConstraint(
            "weight_kg IS NULL OR weight_kg >= 0", name=op.f("ck_setups_weight_nonnegative")
        ),
        sa.CheckConstraint(
            "payload_kg IS NULL OR payload_kg >= 0", name=op.f("ck_setups_payload_nonnegative")
        ),
        sa.CheckConstraint(
            "battery_voltage IS NULL OR battery_voltage >= 0",
            name=op.f("ck_setups_battery_voltage_nonnegative"),
        ),
        sa.CheckConstraint(
            "battery_capacity_ah IS NULL OR battery_capacity_ah >= 0",
            name=op.f("ck_setups_battery_capacity_nonnegative"),
        ),
        sa.CheckConstraint(
            "flight_time_minutes IS NULL OR flight_time_minutes >= 0",
            name=op.f("ck_setups_flight_time_nonnegative"),
        ),
        sa.CheckConstraint(
            "average_current_a IS NULL OR average_current_a >= 0",
            name=op.f("ck_setups_average_current_nonnegative"),
        ),
        sa.CheckConstraint(
            "max_current_a IS NULL OR max_current_a >= 0",
            name=op.f("ck_setups_max_current_nonnegative"),
        ),
        sa.CheckConstraint(
            "average_current_a IS NULL OR max_current_a IS NULL OR "
            "max_current_a >= average_current_a",
            name=op.f("ck_setups_current_order"),
        ),
    )
    op.create_index("ix_setups_status", "setups", ["status"])

    op.create_table(
        "project_setups",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("setup_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_project_setups"),
        sa.UniqueConstraint("project_id", "setup_id", name="uq_project_setups_project_setup_pair"),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_project_setups_project_id_projects",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["setup_id"],
            ["setups.id"],
            name="fk_project_setups_setup_id_setups",
            ondelete="RESTRICT",
        ),
    )
    op.create_index("ix_project_setups_setup_id", "project_setups", ["setup_id"])

    op.create_table(
        "setup_components",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("setup_id", sa.Uuid(), nullable=False),
        sa.Column("component_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("position", sa.String(100), server_default="", nullable=False),
        sa.Column("notes", sa.Text(), server_default="", nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_setup_components"),
        sa.UniqueConstraint(
            "setup_id",
            "component_id",
            "position",
            name="uq_setup_components_setup_component_position",
        ),
        sa.ForeignKeyConstraint(
            ["setup_id"],
            ["setups.id"],
            name="fk_setup_components_setup_id_setups",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["component_id"],
            ["components.id"],
            name="fk_setup_components_component_id_components",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("quantity > 0", name=op.f("ck_setup_components_quantity_positive")),
    )
    op.create_index("ix_setup_components_component_id", "setup_components", ["component_id"])

    op.create_table(
        "firmware_revisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("setup_id", sa.Uuid(), nullable=False),
        sa.Column("version_name", sa.String(255), nullable=False),
        sa.Column("firmware_type", sa.String(255), nullable=False),
        sa.Column("firmware_version", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("config_text", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_firmware_revisions"),
        sa.UniqueConstraint("setup_id", "version_name", name="uq_firmware_revisions_setup_version"),
        sa.UniqueConstraint("setup_id", "id", name="uq_firmware_revisions_setup_id_pair"),
        sa.ForeignKeyConstraint(
            ["setup_id"],
            ["setups.id"],
            name="fk_firmware_revisions_setup_id_setups",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
            name="fk_firmware_revisions_created_by_id_users",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "length(trim(version_name)) > 0",
            name=op.f("ck_firmware_revisions_version_name_nonempty"),
        ),
        sa.CheckConstraint(
            "length(trim(firmware_type)) > 0",
            name=op.f("ck_firmware_revisions_firmware_type_nonempty"),
        ),
        sa.CheckConstraint(
            "length(trim(firmware_version)) > 0",
            name=op.f("ck_firmware_revisions_firmware_version_nonempty"),
        ),
    )
    op.create_index("ix_firmware_revisions_created_by_id", "firmware_revisions", ["created_by_id"])


def downgrade() -> None:
    op.drop_table("firmware_revisions")
    op.drop_table("setup_components")
    op.drop_table("project_setups")
    op.drop_table("setups")
    op.drop_table("components")
