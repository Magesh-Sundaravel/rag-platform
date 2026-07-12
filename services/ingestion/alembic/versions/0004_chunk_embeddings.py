"""pgvector extension, chunk embedding column, HNSW index.

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Enable pgvector and add the embedding column + HNSW index."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column("chunks", sa.Column("embedding", Vector(768), nullable=True))
    op.create_index(
        "ix_chunks_embedding_hnsw",
        "chunks",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    """Drop the HNSW index and embedding column."""
    op.drop_index("ix_chunks_embedding_hnsw", table_name="chunks")
    op.drop_column("chunks", "embedding")
