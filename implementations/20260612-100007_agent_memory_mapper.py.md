# Goal

Replace the `sqlite3.Row | dict[str, Any]` parameter type of `row_to_entry()` with
a strict typed intermediary, and remove `or ""` / `or 0` silent fallbacks for
optional fields.

# Scope

- `scripts/agent/memory/mapper.py`

# Assumptions

1. `row_to_entry(row: sqlite3.Row | dict[str, Any])` currently converts its arg to
   `dict` via `dict(row)` on the first line. Required fields already use `_require()`
   which raises `MemorySchemaError` on KeyError. Optional fields use `d.get("field") or ""`
   which silently treats `None` and `""` as equivalent.
2. The `or ""` pattern in optional string fields (`project`, `repo`, `branch`,
   `summary`, `created_at`, `updated_at`) must be replaced with explicit `None`
   handling: if the field is `None` in the DB, use `""` explicitly via
   `d.get("field") if d.get("field") is not None else ""`.
3. The callers (store.py, retriever.py) pass either `sqlite3.Row` (with row_factory)
   or `dict[str, Any]`. After this change they continue to work unchanged because
   `dict(row)` still works for both types. The signature change is a type annotation
   improvement, not a runtime change.
4. No `SqliteMemoryRow` dataclass is added (the plan mentioned it but the added value
   is low since `sqlite3.Row` already provides column-name access). Instead, tighten
   the annotation and fix the `or ""` patterns.

# Implementation

## Target file

`scripts/agent/memory/mapper.py`

## Procedure

1. In `row_to_entry`, replace each `or ""` / `or 0` fallback:

```python
# Before
project=d.get("project") or "",
repo=d.get("repo") or "",
branch=d.get("branch") or "",
summary=d.get("summary") or "",
created_at=d.get("created_at") or "",
updated_at=d.get("updated_at") or "",
pinned=bool(d.get("pinned", 0)),
```

```python
# After
project=d.get("project") if d.get("project") is not None else "",
repo=d.get("repo") if d.get("repo") is not None else "",
branch=d.get("branch") if d.get("branch") is not None else "",
summary=d.get("summary") if d.get("summary") is not None else "",
created_at=str(_require(d, "created_at")),   # NOT NULL in schema
updated_at=str(_require(d, "updated_at")),   # NOT NULL in schema
pinned=bool(d.get("pinned") or False),       # nullable int column
```

2. Change `pinned` to use:
   ```python
   pinned_raw = d.get("pinned")
   pinned = bool(pinned_raw) if pinned_raw is not None else False
   ```

3. Tighten type annotation of `row_to_entry` to clarify the accepted types:
   ```python
   def row_to_entry(row: sqlite3.Row | dict[str, Any]) -> MemoryEntry:
   ```
   (Annotation unchanged but add a note that callers should ensure `created_at`
    and `updated_at` are always present.)

4. Run ruff + mypy.

## Method

Replace silent `or ""` coercions with explicit `None`-to-`""` mappings, and promote
`created_at`/`updated_at` to required fields via `_require()`.

# Validation plan

- `grep -n " or \"\"" scripts/agent/memory/mapper.py` → 0 hits
- `grep -n " or 0" scripts/agent/memory/mapper.py` → 0 hits
- `uv run ruff check scripts/agent/memory/mapper.py`
- `uv run mypy scripts/agent/memory/mapper.py`
- `uv run pytest tests/test_memory_store.py tests/test_jsonl_store.py -v`
