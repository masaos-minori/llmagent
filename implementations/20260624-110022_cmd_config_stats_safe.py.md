# Implementation Procedure: scripts/agent/commands/cmd_config_stats.py

## Goal

繰り返しの `x if obj is not None else 0` 三項演算子を `_safe()` ヘルパーで置き換える。

## Scope

**In:**
- `scripts/agent/commands/cmd_config_stats.py` — `_safe()` ヘルパー追加; lines 67-85 を一括置換

**Out:** stats 出力の再設計

## Implementation

### _safe ヘルパー (module-level に追加)

```python
from typing import TypeVar
_T = TypeVar("_T")

def _safe(obj: object | None, attr: str, default: _T) -> _T:
    """Return getattr(obj, attr) if obj is not None, else default."""
    return getattr(obj, attr) if obj is not None else default
```

### lines 67-85 — ternary → _safe 置換

```python
# Before:
llm_retries=llm.stat_retries if llm is not None else 0,
llm_reconnects=llm.stat_reconnects if llm is not None else 0,
# ... etc

# After:
llm_retries=_safe(llm, "stat_retries", 0),
llm_reconnects=_safe(llm, "stat_reconnects", 0),
llm_heartbeat_timeouts=_safe(llm, "stat_heartbeat_timeouts", 0),
llm_partial_completions=_safe(llm, "stat_partial_completions", 0),
llm_parse_errors=_safe(llm, "stat_parse_errors", 0),
cache_hits=_safe(ctx.services.tools, "stat_cache_hits", 0),
compress_count=_safe(ctx.services.hist_mgr, "stat_compress_count", 0),
fallback_truncate_count=_safe(ctx.services.hist_mgr, "stat_fallback_truncate_count", 0),
memory_consistency_failures=_safe(ctx.stats, "stat_memory_consistency_failures", 0),
approval_pending=_safe(ctx.workflow, "approval_pending", False),
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/commands/cmd_config_stats.py` | 0 errors |
| Tests | `uv run pytest tests/ -k "config" -x -q` | all pass |
