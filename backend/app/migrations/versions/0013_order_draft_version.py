"""order draft optimistic version

Revision: 0013_order_draft_version
Revises: 0012_product_variants
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013_order_draft_version"
down_revision: str | Sequence[str] | None = "0012_product_variants"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column("draft_version", sa.Integer(), server_default="1", nullable=False),
    )
    op.create_check_constraint("ck_orders_draft_version_positive", "orders", "draft_version > 0")


def downgrade() -> None:
    op.drop_constraint("ck_orders_draft_version_positive", "orders", type_="check")
    op.drop_column("orders", "draft_version")
