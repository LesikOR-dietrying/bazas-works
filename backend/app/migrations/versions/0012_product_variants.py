"""product variants and revision ownership

Revision: 0012_product_variants
Revises: 0011_phase5_execution
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012_product_variants"
down_revision: str | Sequence[str] | None = "0011_phase5_execution"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product_variants",
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("current_revision_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(trim(code)) > 0", name=op.f("ck_product_variants_code_nonempty")
        ),
        sa.CheckConstraint(
            "length(trim(name)) > 0", name=op.f("ck_product_variants_name_nonempty")
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_product_variants_product_id_products"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["current_revision_id"],
            ["product_revisions.id"],
            name="fk_product_variants_current_revision_id_product_revisions",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product_variants")),
        sa.UniqueConstraint("product_id", "code", name="uq_product_variants_product_code"),
        sa.UniqueConstraint("product_id", "id", name="uq_product_variants_product_id_pair"),
    )
    op.create_index(
        op.f("ix_product_variants_product_id"), "product_variants", ["product_id"], unique=False
    )
    op.create_index(
        op.f("ix_product_variants_current_revision_id"),
        "product_variants",
        ["current_revision_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_product_variants_current_revision_id_product_revisions",
        "product_variants",
        "product_revisions",
        ["current_revision_id"],
        ["id"],
        ondelete="RESTRICT",
        use_alter=True,
    )
    op.execute(
        """
        INSERT INTO product_variants
            (id, product_id, code, name, description, is_active, current_revision_id)
        SELECT (md5(id::text || '-standard'))::uuid, id, 'STANDARD', 'Стандартна',
               'Базова комплектація', true, current_revision_id
        FROM products
        """
    )
    op.add_column("product_revisions", sa.Column("variant_id", sa.Uuid(), nullable=True))
    op.execute(
        """
        UPDATE product_revisions AS revision
        SET variant_id = variant.id
        FROM product_variants AS variant
        WHERE variant.product_id = revision.product_id AND variant.code = 'STANDARD'
        """
    )
    op.alter_column("product_revisions", "variant_id", nullable=False)
    op.create_foreign_key(
        op.f("fk_product_revisions_variant_id_product_variants"),
        "product_revisions",
        "product_variants",
        ["variant_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_product_revisions_product_variant",
        "product_revisions",
        "product_variants",
        ["product_id", "variant_id"],
        ["product_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        op.f("ix_product_revisions_variant_id"),
        "product_revisions",
        ["variant_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_product_revisions_variant_code",
        "product_revisions",
        ["variant_id", "revision_code"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_product_revisions_variant_code", "product_revisions", type_="unique")
    op.drop_index(op.f("ix_product_revisions_variant_id"), table_name="product_revisions")
    op.drop_constraint(
        "fk_product_revisions_product_variant", "product_revisions", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_product_revisions_variant_id_product_variants"),
        "product_revisions",
        type_="foreignkey",
    )
    op.drop_column("product_revisions", "variant_id")
    op.drop_constraint(
        "fk_product_variants_current_revision_id_product_revisions",
        "product_variants",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_product_variants_current_revision_id"), table_name="product_variants")
    op.drop_index(op.f("ix_product_variants_product_id"), table_name="product_variants")
    op.drop_table("product_variants")
