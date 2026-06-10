# Implementation: db/tool_results.py — rename args_json → args_masked

## Goal

Rename the `args_json` parameter and all SQL column references in `ToolResultStore` to `args_masked` so that the stored value reflects that sensitive fields have been masked before persistence.

## Scope

- `scripts/db/tool_results.py` — rename parameter `args_json` → `args_masked`; update INSERT and SELECT SQL column names
- No logic changes; only identifier renames

## Assumptions

1. All callers of `ToolResultStore.store()` will be updated in a coordinated commit (see `agent_tool_runner_py.md`, `agent_error_injection_service_py.md`, `agent_orchestrator_py.md`).
2. The DB column is renamed by `db/create_schema.py` migration (see `db_create_schema_py.md`).
3. The `get()` method returns a dict keyed by column name; callers that read `args_json` from that dict must also be updated (`cmd_tooling.py`).

## Implementation

### Target file

`scripts/db/tool_results.py`

### Procedure

1. Read the current file.
2. Apply the following changes.
3. Run `uv run ruff check scripts/db/tool_results.py --fix` and `uv run mypy scripts/db/tool_results.py`.

### Method

Rename all occurrences of `args_json` to `args_masked` within this file.

### Details

**`store()` method — parameter rename:**
```python
# BEFORE (line ~25)
def store(
    self,
    session_id: int | None,
    turn: int,
    tool_name: str,
    args_json: str,
    ...
) -> int | None:

# AFTER
def store(
    self,
    session_id: int | None,
    turn: int,
    tool_name: str,
    args_masked: str,
    ...
) -> int | None:
```

**`store()` method — INSERT SQL:**
```python
# BEFORE
"INSERT INTO tool_results"
" (session_id, turn, tool_name, args_json,"
"  full_text, summary, is_error)"
" VALUES (?, ?, ?, ?, ?, ?, ?)",

# AFTER
"INSERT INTO tool_results"
" (session_id, turn, tool_name, args_masked,"
"  full_text, summary, is_error)"
" VALUES (?, ?, ?, ?, ?, ?, ?)",
```

**`store()` method — tuple binding:**
```python
# BEFORE (the positional tuple passed to execute)
(session_id, turn, tool_name, args_json, full_text, summary, int(is_error))

# AFTER
(session_id, turn, tool_name, args_masked, full_text, summary, int(is_error))
```

**`get()` method — SELECT SQL:**
```python
# BEFORE
"SELECT id, session_id, turn, tool_name, args_json,"
" full_text, summary, is_error, created_at"
" FROM tool_results WHERE id = ?",

# AFTER
"SELECT id, session_id, turn, tool_name, args_masked,"
" full_text, summary, is_error, created_at"
" FROM tool_results WHERE id = ?",
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/db/tool_results.py` | 0 errors |
| Type | `uv run mypy scripts/db/tool_results.py` | no new errors |
| Unit tests | `uv run pytest tests/test_tool_result_store.py -v` | all pass (requires test update in `test_tool_result_store_py.md`) |
