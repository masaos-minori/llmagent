# Implementation: agent/tool_runner.py — use masked args + rename kwarg; orchestrator.py and error_injection_service.py kwarg updates

## Goal

In `_collect_tool_result_msgs()`, pass `masked` (already computed at line 97) instead of raw `args` when storing to `ToolResultStore`. Update the keyword argument name from `args_json` to `args_masked` at all three call sites.

## Scope

- `scripts/agent/tool_runner.py` — change `args_json=orjson.dumps(args)` to `args_masked=orjson.dumps(masked)` in `_collect_tool_result_msgs()`
- `scripts/agent/orchestrator.py` — rename kwarg `args_json="{}"` to `args_masked="{}"`
- `scripts/agent/error_injection_service.py` — rename kwarg `args_json="{}"` to `args_masked="{}"`

## Assumptions

1. `masked = mask_args(args, ctx.cfg.tool.masked_fields)` is already computed at line 97 of `tool_runner.py`, before the `ToolResultStore.store()` call at line 108.
2. `ToolResultStore.store()` parameter is renamed to `args_masked` in `db_tool_results_py.md`.
3. `orchestrator.py:254` and `error_injection_service.py:52` use `args_json="{}"` (empty dict, no sensitive data), so masking is a no-op there — only the kwarg name changes.

## Implementation

### Target file

`scripts/agent/tool_runner.py` (primary), `scripts/agent/orchestrator.py`, `scripts/agent/error_injection_service.py`

### Procedure

1. Read `scripts/agent/tool_runner.py`.
2. Edit the `ToolResultStore.store()` call in `_collect_tool_result_msgs()`.
3. Read and edit `scripts/agent/orchestrator.py` (one line).
4. Read and edit `scripts/agent/error_injection_service.py` (one line).
5. Run ruff + mypy on all three files.

### Method

Single-line edits at the identified call sites.

### Details

**`scripts/agent/tool_runner.py` — line ~112:**
```python
# BEFORE
        result_id = ctx.tool_result_store.store(
            session_id=ctx.session.session_id,
            turn=turn,
            tool_name=name,
            args_json=orjson.dumps(args).decode(),
            full_text=text,
            summary=llm_text if summarized else None,
            is_error=is_error,
        )

# AFTER
        result_id = ctx.tool_result_store.store(
            session_id=ctx.session.session_id,
            turn=turn,
            tool_name=name,
            args_masked=orjson.dumps(masked).decode(),
            full_text=text,
            summary=llm_text if summarized else None,
            is_error=is_error,
        )
```

**`scripts/agent/orchestrator.py` — line ~250-258:**
```python
# BEFORE
        ctx.tool_result_store.store(
            session_id=ctx.session.session_id,
            turn=ctx.stats.stat_turns,
            tool_name="llm_partial_completion",
            args_json="{}",
            ...
        )

# AFTER
        ctx.tool_result_store.store(
            session_id=ctx.session.session_id,
            turn=ctx.stats.stat_turns,
            tool_name="llm_partial_completion",
            args_masked="{}",
            ...
        )
```

**`scripts/agent/error_injection_service.py` — line ~52:**
```python
# BEFORE
        ctx.tool_result_store.store(
            session_id=ctx.session.session_id,
            turn=turn,
            tool_name="llm_transport_error",
            args_json="{}",
            ...
        )

# AFTER
        ctx.tool_result_store.store(
            session_id=ctx.session.session_id,
            turn=turn,
            tool_name="llm_transport_error",
            args_masked="{}",
            ...
        )
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/tool_runner.py scripts/agent/orchestrator.py scripts/agent/error_injection_service.py` | 0 errors |
| Type | `uv run mypy scripts/agent/tool_runner.py` | no new errors |
| Unit tests | `uv run pytest tests/test_tool_runner.py -v` | all pass |
| Security | verify no raw `args` dict is stored (only `masked`) | manual diff review |
