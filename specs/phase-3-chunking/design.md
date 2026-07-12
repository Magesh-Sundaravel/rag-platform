# Phase 3 Design

## Chunker implementations (`processing/chunking.py`)

```python
class Chunker(Protocol):
    def chunk(self, text: str) -> list[str]: ...
```

- `FixedSizeChunker`: window `[i, i+size)`, step `size - overlap`; drops a
  trailing window already fully covered by the previous one.
- `RecursiveCharacterChunker`: separators `["\n\n", "\n", ". ", " "]`;
  recursively split any piece > size with the next separator (hard cut at
  the last level), then greedily merge adjacent pieces to ≤ size, prefixing
  each subsequent chunk with the last `overlap` characters of the previous.
- `build_chunker(settings)` — factory mapping strategy name → instance;
  unknown name raises `InvalidInputError` at startup.

## Persistence

- `rag_db.models.Chunk` with `PortableJSON` metadata (JSONB on Postgres).
- Migration `0002_chunks` (same lineage).
- `pipeline.process_document`: delete existing chunks for the document,
  insert new rows with `chunk_index` and `token_count`
  (`metadata.estimate_tokens`), chunk metadata `{title, language, filename}`.

## Config

`processing.Settings`: `chunk_strategy: Literal["fixed", "recursive"] =
"recursive"`, `chunk_size: int = 1200`, `chunk_overlap: int = 200`.
