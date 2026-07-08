# Implementation: H-7 — Remove tool_result_store mock setup from test_agent_repl_tool_exec.py

## Goal

Remove the now-unnecessary `ctx.tool_result_store = MagicMock()` line from this file's shared
context-building helper, since `AgentContext` no longer has that field.

## Scope

**Target**: `tests/test_agent_repl_tool_exec.py`

**Depends on**: `scripts/agent/context.py`'s H-7 change (field removal).

**Out of scope**: every other line in this file's context helper and all test method bodies —
none of them reference `tool_result_store` beyond the one mock-setup line (confirmed by grep:
single match in the whole file).

## Assumptions

1. `ctx.tool_result_store = MagicMock()` (line 343) is pure setup with no corresponding
   assertion anywhere in this file — removing it changes no test outcome, since `ctx` is a
   `MagicMock()`-based object elsewhere in the helper and no test reads
   `ctx.tool_result_store` after this line.

## Implementation

### Target file

`tests/test_agent_repl_tool_exec.py`

### Procedure

#### Step 1: Confirm the single occurrence

```bash
grep -n "tool_result_store" tests/test_agent_repl_tool_exec.py
```

Expected: exactly one match, line 343.

#### Step 2: Remove the line

Current (within the shared context-building helper, lines 335-344):

```python
    ctx.cfg.tool.tool_results_turn_max_chars = 50000
    ctx.cfg.tool.use_tool_summarize = False
    ctx.cfg.tool.tool_summarize_threshold = 0
    ctx.conv.history = []
    ctx.services = MagicMock()
    ctx.services_required.gateway = None
    ctx.session = MagicMock()
    ctx.session.save_many = MagicMock()
    ctx.tool_result_store = MagicMock()
    return ctx
```

Replace with:

```python
    ctx.cfg.tool.tool_results_turn_max_chars = 50000
    ctx.cfg.tool.use_tool_summarize = False
    ctx.cfg.tool.tool_summarize_threshold = 0
    ctx.conv.history = []
    ctx.services = MagicMock()
    ctx.services_required.gateway = None
    ctx.session = MagicMock()
    ctx.session.save_many = MagicMock()
    return ctx
```

### Method

- Single-line deletion; no other change to the helper or any test method.

### Details

- `ctx.cfg.tool.use_tool_summarize = False` and `ctx.cfg.tool.tool_summarize_threshold = 0`
  (the two lines immediately above the removed one) remain in the helper even though the
  companion H-1 change removes the summarize branch from `tool_runner.py` entirely — these
  config fields still exist on `AgentConfig` (H-1 explicitly keeps them; only their read sites in
  `execute_one_tool_call()` are removed) and setting them here remains harmless.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check tests/test_agent_repl_tool_exec.py` | 0 errors |
| Type check | `mypy tests/test_agent_repl_tool_exec.py` | no new errors |
| Grep (line removed) | `grep -n "tool_result_store" tests/test_agent_repl_tool_exec.py` | no matches |
| Tests (targeted) | `uv run pytest tests/test_agent_repl_tool_exec.py -v` | all pass, no behavior change |
| Tests (full) | `uv run pytest -v` | no new failures |
| Pre-commit | `pre-commit run --all-files` | pass |
