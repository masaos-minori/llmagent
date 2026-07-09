# Implementation: Move `stat_partial_completions` to `RuntimeStats`

## Goal

Relocate `stat_partial_completions` from `LLMClient` to `RuntimeStats` (`ctx.stats`), removing the single `LLMClient` stat outlier and its associated None-guards.

## Scope

- `scripts/agent/context.py` — add field
- `scripts/shared/llm_client.py` — remove field and increment
- `scripts/agent/llm_transport_errors.py` — redirect increment
- `scripts/agent/repl.py` — redirect reads
- `scripts/agent/services/context_view.py` — redirect read
- `scripts/agent/commands/cmd_config_stats.py` — redirect stat display

## Assumptions

- No tests or other code references `stat_partial_completions` on `LLMClient` directly.
- `RuntimeStats` is in-memory only; moving the field does not change persistence.

## Implementation

### Step 1: Add field to `RuntimeStats`

Target file: `scripts/agent/context.py`

Procedure: Add `stat_partial_completions: int = 0` after the existing `stat_memory_fts_fallback_count` field.

Method: Insert a new line in the `RuntimeStats` dataclass.

### Step 2: Remove field and increment from `LLMClient`

Target file: `scripts/shared/llm_client.py`

Procedure:
- Remove `self.stat_partial_completions: int = 0` from `__init__`.
- Remove `self.stat_partial_completions += partial_completions` from `_increment_stats`.

### Step 3: Redirect increment in `llm_transport_errors.py`

Target file: `scripts/agent/llm_transport_errors.py`

Procedure: Change `ctx.services_required.llm.stat_partial_completions += 1` to `ctx.stats.stat_partial_completions += 1`.

### Step 4: Redirect reads in `repl.py`

Target file: `scripts/agent/repl.py`

Procedure:
- Line ~241: Change `llm.stat_partial_completions if llm is not None else 0` to `stats.stat_partial_completions`.
- Line ~408: Change `llm.stat_partial_completions if llm is not None else 0` to `ctx.stats.stat_partial_completions`.
- Line ~410: Change `llm.stat_partial_completions > _prev_partial` to `ctx.stats.stat_partial_completions > _prev_partial`.

### Step 5: Redirect read in `context_view.py`

Target file: `scripts/agent/services/context_view.py`

Procedure: Replace the guard expression `ctx.services_required.llm.stat_partial_completions if ctx.services is not None and ctx.services_required.llm is not None else 0` with `ctx.stats.stat_partial_completions`.

### Step 6: Redirect stat display in `cmd_config_stats.py`

Target file: `scripts/agent/commands/cmd_config_stats.py`

Procedure: Change `_safe(llm, "stat_partial_completions", 0)` to `ctx.stats.stat_partial_completions`.

## Validation plan

1. `uv run python -m compileall -q scripts/` — syntax check
2. `uv run ruff check scripts/` — lint clean
3. `uv run mypy scripts/` — type safe (no new errors vs pre-existing)
4. `uv run pytest -v` — full test suite passes
5. `grep -rn "llm.*stat_partial_completions" scripts/` — returns 0 (no leftover references)
