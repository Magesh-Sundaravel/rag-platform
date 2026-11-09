"""Switch chunk embeddings to Bedrock's 1024-dimensional default.

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-22
"""

from collections.abc import Sequence

from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Resize chunk embeddings to 1024 dims and rebuild the HNSW index.

    Existing embeddings are cleared because vectors generated at 768
    dimensions cannot be reused with the new Bedrock model.
    """
    op.drop_index("ix_chunks_embedding_hnsw", table_name="chunks")
    op.execute("UPDATE chunks SET embedding = NULL")
    op.alter_column("chunks", "embedding", existing_type=Vector(768), type_=Vector(1024))
    op.create_index(
        "ix_chunks_embedding_hnsw",
        "chunks",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    """Restore the previous 768-dimensional embedding column."""
    op.drop_index("ix_chunks_embedding_hnsw", table_name="chunks")
    op.execute("UPDATE chunks SET embedding = NULL")
    op.alter_column("chunks", "embedding", existing_type=Vector(1024), type_=Vector(768))
    op.create_index(
        "ix_chunks_embedding_hnsw",
        "chunks",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
