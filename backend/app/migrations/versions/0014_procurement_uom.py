"""procurement units of measure

Revision: 0014_procurement_uom
Revises: 0013_order_draft_version
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014_procurement_uom"
down_revision: str | Sequence[str] | None = "0013_order_draft_version"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("procurement_records", sa.Column("uom_id", sa.Uuid(), nullable=True))
    op.execute(
        """
        UPDATE procurement_records AS procurement
        SET uom_id = component.default_uom_id
        FROM components AS component
        WHERE component.id = procurement.component_id
        """
    )
    op.alter_column("procurement_records", "uom_id", nullable=False)
    op.create_foreign_key(
        op.f("fk_procurement_records_uom_id_units_of_measure"),
        "procurement_records",
        "units_of_measure",
        ["uom_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        op.f("ix_procurement_records_uom_id"),
        "procurement_records",
        ["uom_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_procurement_records_uom_id"), table_name="procurement_records")
    op.drop_constraint(
        op.f("fk_procurement_records_uom_id_units_of_measure"),
        "procurement_records",
        type_="foreignkey",
    )
    op.drop_column("procurement_records", "uom_id")
