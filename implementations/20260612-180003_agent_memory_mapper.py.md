# Goal

Replace `str(v)` in `_opt_str()` with an isinstance guard that raises
`MemorySchemaError` on unexpected types, and replace `str(_require(d, "memory_id"))`
/ `str(_require(d, "content"))` with explicit isinstance validation.

# Scope

- `scripts/agent/memory/mapper.py`

# Assumptions

1. `_opt_str` is used for nullable DB TEXT columns. Values from sqlite3 for these
   columns are always `str` or `None`. The `str(v)` coercion silently hides bugs;
   replacing with isinstance raises immediately.
2. `str(_require(d, "memory_id"))` and `str(_require(d, "content"))` — both
   are NOT NULL TEXT columns in the DB. `sqlite3` returns TEXT as `str`.
   Adding isinstance validation makes this explicit.
3. `str(_require(d, "memory_type"))` and `str(_require(d, "source_type"))` are
   passed to StrEnum constructors (`MemoryType()`, `SourceType()`). Keep `str()`
   cast here — StrEnum constructor requires str, and the coercion is intentional
   for clarity (even though the value should already be str).
4. `MemorySchemaError` is already imported in this file.

# Implementation

## Target file

`scripts/agent/memory/mapper.py`

## Procedure

1. Replace `_opt_str` body (line 22):
   ```python
   # Before
   def _opt_str(d: dict[str, Any], key: str) -> str:
       """Return string value for key, or "" if absent or None."""
       v = d.get(key)
       return str(v) if v is not None else ""

   # After
   def _opt_str(d: dict[str, Any], key: str) -> str:
       """Return string value for key, or "" if absent or None; raises MemorySchemaError on wrong type."""
       v = d.get(key)
       if v is None:
           return ""
       if not isinstance(v, str):
           raise MemorySchemaError(
               f"Field {key!r} must be str or None, got {type(v).__name__}"
           )
       return v
   ```

2. Replace `str(_require(d, "memory_id"))` (line 67):
   ```python
   # Before
   memory_id=str(_require(d, "memory_id")),

   # After
   _mid = _require(d, "memory_id")
   if not isinstance(_mid, str):
       raise MemorySchemaError(
           f"memory_id must be str, got {type(_mid).__name__}"
       )
   ```
   Then use `memory_id=_mid,` in the constructor.

3. Replace `str(_require(d, "content"))` (line 75):
   ```python
   # Before
   content=str(_require(d, "content")),

   # After
   _content = _require(d, "content")
   if not isinstance(_content, str):
       raise MemorySchemaError(
           f"content must be str, got {type(_content).__name__}"
       )
   ```
   Then use `content=_content,` in the constructor.

4. Run ruff + mypy.

## Method

`_opt_str` body replacement (4 lines → 7 lines).
Two `str(_require(...))` → separate validation + bare variable.

# Validation plan

- `grep -n "str(v)\|str(_require(d, .memory_id\|str(_require(d, .content" scripts/agent/memory/mapper.py` → 0 hits
- `uv run ruff check scripts/agent/memory/mapper.py`
- `uv run mypy scripts/agent/memory/mapper.py`
- `uv run pytest tests/test_memory_store.py -v`
