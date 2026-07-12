"""Shared database layer: SQLAlchemy models and async session helpers.

All services share one Postgres instance in the MVP (ADR-0004); this library
keeps the "services never import each other" rule intact by hosting the
shared ORM models.
"""

__version__ = "0.1.0"
