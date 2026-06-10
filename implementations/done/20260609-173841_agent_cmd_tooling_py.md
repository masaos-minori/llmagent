# Implementation: agent/commands/cmd_tooling.py — rename args_json reference to args_masked

## Goal

Update the `_tool_show()` method to read `args_masked` from the dict returned by `ToolResultStore.get()` instead of `args_json`.

## Scope

- `scripts/agent/commands/cmd_tooling.py` — one line change in `_tool_show()`

## Assumptions

1. `ToolResultStore.get()` returns a dict keyed by SQLite column names. After the DB migration (`args_json` → `args_masked`), the dict will have key `"args_masked"`.
2. No other references to `args_json` exist in this file.

## Implementation

### Target file

`scripts/agent/commands/cmd_tooling.py`

### Procedure

1. Read the file.
2. Edit line ~50.
3. Run ruff + mypy.

### Method

Single-line edit in `_tool_show()`.

### Details

```python
# BEFORE (line ~50)
        try:
            args_obj = orjson.loads(result.get("args_json") or "{}")
        except orjson.JSONDecodeError:
            args_obj = {}

# AFTER
        try:
            args_obj = orjson.loads(result.get("args_masked") or "{}")
        except orjson.JSONDecodeError:
            args_obj = {}
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/commands/cmd_tooling.py` | 0 errors |
| Type | `uv run mypy scripts/agent/commands/cmd_tooling.py` | no new errors |
| Unit tests | `uv run pytest tests/test_agent_rag.py -v` | all pass |
