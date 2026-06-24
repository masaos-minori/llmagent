# Agent Extension Points — Fallback Truncation Count in /stats and Session Diagnostics

## Goal

Expose `stat_fallback_truncate_count` in `/stats` output and session-end diagnostics so operators can distinguish successful LLM compression from deterministic fallback truncation without reading the Python log file.

## Scope

**In:**
- `scripts/agent/commands/models.py` — add `fallback_truncate_count: int = 0` to `StatsViewModel`
- `scripts/agent/commands/cmd_config_stats.py` — read `stat_fallback_truncate_count` in `_collect_stats()` and display it in `_cmd_stats()`
- `scripts/agent/repl.py` — add `fallback_truncate_count` to `_persist_session_diagnostics()` output

**Out:**
- Implementing `_fallback_truncate()` (already exists in `history.py`)
- Changing `/context` display (already shows `Fallback trunc: N` via `context_view.py`)
- Replacing LLM-based compression
- Redesigning history scoring

## Assumptions

1. The entire fallback truncation implementation already exists and is correct:
   - `history.py:_fallback_truncate()` drops lowest-importance messages first, preserves protect_turns
   - `CompressResult.is_fallback: bool = False` field
   - `stat_fallback_truncate_count: int` counter in `HistoryManager`
   - `compress()` calls `_fallback_truncate()` when LLM summary returns `None` and still over char limit
   - `/context` shows `Fallback trunc: N` via `ContextStateView.fallback_truncate_count`
   - All tests for fallback logic exist in `test_history_manager.py`
2. The only visibility gap is in `/stats` (shows `Compress` but not `Fallback trunc`) and session-end diagnostics JSON.
3. `StatsViewModel` is a `@dataclass(frozen=True)` — adding a field with a default value does not break existing instantiations.

## Implementation

### Target file: `scripts/agent/commands/models.py`

**Procedure:** Add `fallback_truncate_count: int = 0` to `StatsViewModel` dataclass.

**Method:** Place immediately after `compress_count` for logical grouping.

**Details:**
```python
@dataclass(frozen=True)
class StatsViewModel:
    ...
    compress_count: int
    fallback_truncate_count: int = 0   # add this line
    ...
```

### Target file: `scripts/agent/commands/cmd_config_stats.py`

**Procedure:** Read `stat_fallback_truncate_count` in `_collect_stats()` and display it in `_cmd_stats()`.

**Method:** Follow the same null-guard pattern used for `compress_count`.

**Details:**
In `_collect_stats()`, add after `compress_count=...`:
```python
fallback_truncate_count=ctx.services.hist_mgr.stat_fallback_truncate_count
if ctx.services.hist_mgr is not None
else 0,
```

In `_cmd_stats()`, add after the `Compress` line:
```python
self._out.write(f"  Fallback trunc: {stats.fallback_truncate_count}")
```

This places it directly below `Compress` so operators can compare the two values at a glance.

### Target file: `scripts/agent/repl.py`

**Procedure:** Add `fallback_truncate_count` to `_persist_session_diagnostics()` summary dict.

**Method:** Follow the same null-guard pattern used for `compress_count`.

**Details:**
In the `summary` dict (around line 265), add alongside `compress_count`:
```python
"compress_count": (
    hist_mgr.stat_compress_count if hist_mgr is not None else 0
),
"fallback_truncate_count": (
    hist_mgr.stat_fallback_truncate_count if hist_mgr is not None else 0
),
```

## Validation Plan

| Check | Tool | Target |
|---|---|---|
| Lint | `ruff check scripts/agent/commands/` | 0 errors |
| Type check | `mypy scripts/agent/commands/cmd_config_stats.py` | no new errors |
| Tests | `uv run pytest tests/test_agent_cmd_config.py -v` | all pass |
| Tests | `uv run pytest tests/test_history_manager.py -v` | no regression |
