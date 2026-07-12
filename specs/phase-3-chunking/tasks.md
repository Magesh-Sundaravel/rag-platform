# Phase 3 Tasks

1. `Chunk` model + migration 0002. → verify: sqlite create_all + CI alembic.
2. `chunking.py`: protocol, FixedSizeChunker, RecursiveCharacterChunker, factory. → verify: invariant unit tests.
3. Settings: strategy/size/overlap. → verify: config test.
4. Pipeline: chunk + persist + idempotent replace. → verify: worker test asserts chunk rows.
5. Docs/status; gates; commit; push; CI green.
