# Implementation: memory/jsonl_store.py — malformed line fail-fast

## Goal

Remove `_entry_from_dict`'s `except Exception: return None` silent failure.
Add `strict` parameter to `read_all()`: strict=True raises on malformed, strict=False
writes malformed lines to a quarantine file and continues.

## Scope

- `scripts/agent/memory/jsonl_store.py` — primary
- `tests/test_memory_jsonl.py` — update tests that expect silent skip

## Assumptions

1. `JsonlMemoryStore` gains an optional `quarantine_path: Path | None = None`.
   When `strict=False` and a malformed line is found:
   - If `quarantine_path` is set: append the raw line to that file.
   - If `quarantine_path` is None: raise `ValueError` (same as strict mode).
2. `_entry_from_dict` no longer catches exceptions; callers handle them.
3. `malformed_count` property is kept for observability but incremented only on skip (non-strict).
4. `write()` is unchanged (append-only, no read involved).

## Implementation

### _entry_from_dict: remove try/except

```python
def _entry_from_dict(d: dict) -> MemoryEntry:
    """Deserialise one JSONL dict to MemoryEntry; raises on validation error."""
    memory_type = d.get("memory_type", "")
    if memory_type not in MEMORY_TYPES:
        raise ValueError(f"Invalid memory_type={memory_type!r}")
    return row_to_entry(d)
```

Returns `MemoryEntry` (not `MemoryEntry | None`).

### read_all: strict parameter + quarantine

```python
def read_all(self, *, strict: bool = False) -> list[MemoryEntry]:
    """Read all entries. If strict=True, raises on first malformed line.
    If strict=False and quarantine_path is set, writes malformed lines there.
    If strict=False and quarantine_path is None, raises on malformed.
    """
```

### __init__: add quarantine_path

```python
def __init__(self, path: str | Path, quarantine_path: str | Path | None = None) -> None:
    self._path = Path(path)
    self._quarantine = Path(quarantine_path) if quarantine_path else None
    self._lock: asyncio.Lock | None = None
    self._malformed_count: int = 0
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/memory/jsonl_store.py` | 0 errors |
| Type | `uv run mypy scripts/agent/memory/jsonl_store.py` | no new errors |
| Tests | `uv run pytest tests/test_memory_jsonl.py -x -v` | all pass |
| No silent skip | `grep -n "except Exception\|return None" scripts/agent/memory/jsonl_store.py` | 0 hits |
