# Implementation: M-1 — Remove use_tool_summarize mock assignments (cleanup)

## Goal

Remove the `ctx.cfg.tool.use_tool_summarize = False` and
`ctx.cfg.tool.tool_summarize_threshold = 0` lines from the shared context helper — these fields
no longer exist on `ToolConfig` after M-1's `config_dataclasses.py` change.

## Scope

**Target**: `tests/test_agent_repl_tool_exec.py` — lines ~336-337.

**Supersedes**: this doc extends `implementations/20260708-164339_test_agent_repl_tool_exec.py.md`
(an H-7 doc for the same file), which explicitly LEFT these two lines in place, reasoning that
`ctx.cfg` there is a `MagicMock()` and setting arbitrary attributes on it is harmless regardless
of what `ToolConfig` actually defines. **That reasoning is still technically correct — this is a
lower-priority cleanup than the other M-1 test-fixture docs, not a required fix** (unlike
`test_tool_runner.py`/`test_tool_policy.py`/etc., which use REAL `build_agent_config()` and would
hard-fail with `ConfigLoadError`). This doc removes the lines purely so the test file does not
reference two fields that no longer exist anywhere in production code, for clarity.

**Depends on**: none (safe to apply independently, before or after
`config_dataclasses.py`'s M-1 change, since `ctx.cfg` here is a `MagicMock()`, not a real
`ToolConfig` instance).

## Assumptions

1. `ctx.cfg` in this test file's shared helper is a `MagicMock()` (confirmed by the H-7 doc's
   own analysis of this same file) — removing these two assignment lines has zero effect on test
   behavior, since no assertion in this file reads `ctx.cfg.tool.use_tool_summarize`/
   `.tool_summarize_threshold` afterward.

## Implementation

### Target file

`tests/test_agent_repl_tool_exec.py`

### Procedure

#### Step 1: Confirm the current lines

```bash
grep -n "use_tool_summarize\|tool_summarize_threshold" tests/test_agent_repl_tool_exec.py
```

Expected: two matches (lines ~336-337).

#### Step 2: Remove both lines

Current:

```python
    ctx.cfg.tool.use_tool_summarize = False
    ctx.cfg.tool.tool_summarize_threshold = 0
```

Remove both lines entirely. Adjacent lines in the same helper function are unaffected.

### Method

- Two-line deletion; purely cosmetic (removes references to fields that no longer exist in
  production, on a `MagicMock` that would silently tolerate them either way).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check tests/test_agent_repl_tool_exec.py` | 0 errors |
| Grep (lines removed) | `grep -n "use_tool_summarize\|tool_summarize_threshold" tests/test_agent_repl_tool_exec.py` | no matches |
| Tests (targeted) | `uv run pytest tests/test_agent_repl_tool_exec.py -v` | all pass (no behavior change) |
| Tests (full) | `uv run pytest -v` | no new failures |
| Pre-commit | `pre-commit run --all-files` | pass |
