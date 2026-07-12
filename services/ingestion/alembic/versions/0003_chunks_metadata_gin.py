"""GIN index on chunks.metadata.

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-12
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the jsonb_path_ops GIN index on chunk metadata."""
    op.create_index(
        "ix_chunks_metadata_gin",
        "chunks",
        ["metadata"],
        postgresql_using="gin",
        postgresql_ops={"metadata": "jsonb_path_ops"},
    )


def downgrade() -> None:
    """Drop the metadata GIN index."""
    op.drop_index("ix_chunks_metadata_gin", table_name="chunks")
