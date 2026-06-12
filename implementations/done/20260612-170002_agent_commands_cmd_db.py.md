# Goal

Replace the five `str(r[...])` unconditional coercions in `_db_list_urls()` with
explicit isinstance checks so that unexpected types from `list_documents()` are
detected at the display boundary.

# Scope

- `scripts/agent/commands/cmd_db.py` — lines 93–105 (`table_rows` list comprehension)

# Assumptions

1. `AgentSession.list_documents()` returns `list[dict]` where each dict has:
   - `url`: str (NOT NULL in DB)
   - `lang`: str | None (nullable)
   - `chunk_count`: int (`COUNT()` always returns int in sqlite3)
   - `fetched_at`: str | None (DB TEXT, nullable)
2. `str(r["lang"] or "?")` treats None and "" as equivalent fallback to `"?"`.
   Keep the fallback logic but remove unconditional `str()` cast:
   `lang_val = r["lang"]; display = lang_val if isinstance(lang_val, str) else "?"`
3. `str(r["chunk_count"])` — `chunk_count` is int from `COUNT()`; format with
   `str(int_val)` is appropriate after isinstance validation.
4. `str(r["fetched_at"])` — `fetched_at` is str | None; if None use `""`.

# Implementation

## Target file

`scripts/agent/commands/cmd_db.py`

## Procedure

Replace lines 93–105 with explicit validation:

```python
table_rows = []
for r in rows:
    url = r["url"]
    if not isinstance(url, str):
        raise TypeError(f"url must be str, got {type(url).__name__}")
    url_display = url[:57] + "..." if len(url) > 60 else url

    lang_val = r["lang"]
    lang_display = lang_val if isinstance(lang_val, str) else "?"

    chunk_count = r["chunk_count"]
    if not isinstance(chunk_count, int):
        raise TypeError(f"chunk_count must be int, got {type(chunk_count).__name__}")
    chunk_display = str(chunk_count)

    fetched_at = r["fetched_at"]
    fetched_display = fetched_at if isinstance(fetched_at, str) else ""

    table_rows.append([url_display, lang_display, chunk_display, fetched_display])
```

## Method

Expand list comprehension into explicit loop with isinstance guards.

# Validation plan

- `grep -n "str(r\[" scripts/agent/commands/cmd_db.py` → 0 hits
- `uv run ruff check scripts/agent/commands/cmd_db.py`
- `uv run mypy scripts/agent/commands/cmd_db.py`
- `uv run pytest tests/test_agent_cmd_db.py -v`
