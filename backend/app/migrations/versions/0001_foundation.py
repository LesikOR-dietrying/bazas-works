"""Migration baseline; business tables arrive with their modules."""

revision: str = "0001_foundation"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # Alembic creates/updates its own version table. No speculative business schema.
    pass


def downgrade() -> None:
    pass
