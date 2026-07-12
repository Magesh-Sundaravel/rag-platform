"""GIN index on to_tsvector('english', chunks.text) for full-text search.

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-12
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the functional GIN index used by Postgres full-text search."""
    op.execute("CREATE INDEX ix_chunks_text_fts ON chunks USING gin (to_tsvector('english', text))")


def downgrade() -> None:
    """Drop the full-text search index."""
    op.execute("DROP INDEX ix_chunks_text_fts")
