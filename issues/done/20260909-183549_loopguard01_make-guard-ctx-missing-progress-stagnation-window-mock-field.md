# `_make_guard_ctx()` in `test_rag_llm_integration.py` omits `progress_stagnation_window`, breaking 2 `ToolLoopGuard` tests

## Priority
Medium

## Summary
`tests/integration/test_rag_llm_integration.py::test_c07_tool_loop_guard_fires_on_dedup`
and `::test_c08_tool_loop_guard_allows_different_args` fail with `TypeError: '<=' not
supported between instances of 'MagicMock' and 'int'`. Confirmed stale test helper: the
shared `_make_guard_ctx()` function sets `ctx.cfg.tool.tool_dedup_max_repeats`,
`ctx.cfg.tool.tool_cycle_detect_window`, and `ctx.cfg.tool.tool_error_retry_max`, but
never sets `ctx.cfg.tool.progress_stagnation_window`. `ToolLoopGuard.check_all()` calls
`self._check_progress_stagnation(...)` (per its own inline comment, "NEW: check
stagnation before dedup/retry"), which reads
`ctx.cfg.tool.progress_stagnation_window <= 0` — since `ctx` is a bare `MagicMock()`,
the unset attribute auto-creates a child `MagicMock` instead of an `int`, and the `<=`
comparison raises `TypeError`.

## Background
`ToolLoopGuard._check_progress_stagnation()` (`scripts/agent/tool_loop_guard.py`) was
added to the guard chain after `_make_guard_ctx()` was written; the helper was never
updated to configure the new check's config field. `ToolConfig`
(`scripts/agent/config_dataclasses.py`) confirms `progress_stagnation_window: int = 3`
is a real, current field — this is not a removed or renamed setting, unlike the flat
keys in `plans/done/20260908-221312_plan.md` (cfgval001).

## Problem
Both tests construct their `ToolLoopGuard` via `_make_guard_ctx()`, which never sets
`progress_stagnation_window`. `check_all()` unconditionally invokes
`_check_progress_stagnation()` before `check_dedup()`/`check_retry()`, so both tests fail
before reaching their actual dedup/args-differentiation assertions.

Reproduction (confirmed by direct execution):
```
uv run pytest tests/integration/test_rag_llm_integration.py -q
# → 2 failed, 7 passed in 0.60s
# test_c07_tool_loop_guard_fires_on_dedup, test_c08_tool_loop_guard_allows_different_args:
# TypeError: '<=' not supported between instances of 'MagicMock' and 'int'
#   at scripts/agent/tool_loop_guard.py::_check_progress_stagnation
```

## Reason for Change
2 tests intended to verify `ToolLoopGuard`'s dedup/args-differentiation behavior
currently provide no real coverage of that behavior — they fail before reaching their
own assertions, and would continue to mask a real dedup/args regression until this
fixture gap is fixed.

## Implementation Intent
Add `ctx.cfg.tool.progress_stagnation_window = <value>` to `_make_guard_ctx()`, using a
value that does not itself trigger stagnation detection during these two tests' specific
call sequences (e.g. a value large enough, or `0` to disable the check per its own
`<= 0` disables semantics — confirm which is correct against
`_check_progress_stagnation()`'s full logic before choosing).

## Target Files or Areas
- `tests/integration/test_rag_llm_integration.py` (`_make_guard_ctx()`)
- `scripts/agent/tool_loop_guard.py` (`_check_progress_stagnation()`) — reference only

## Required Changes
- Add a `progress_stagnation_window` value to `_make_guard_ctx()`'s `ctx.cfg.tool`
  mock setup.
- No change to `scripts/agent/tool_loop_guard.py`.

## Constraints
Do not weaken or bypass `_check_progress_stagnation()`'s logic — it is confirmed
intentional, current behavior; only the test fixture's mock setup is incomplete.

## Acceptance Criteria
- [ ] `_make_guard_ctx()` sets `ctx.cfg.tool.progress_stagnation_window` to a concrete
  `int`
- [ ] `uv run pytest tests/integration/test_rag_llm_integration.py -q` passes with no
  `TypeError` from `_check_progress_stagnation`
- [ ] No change to `scripts/agent/tool_loop_guard.py`

## Testing Expectations
- `uv run pytest tests/integration/test_rag_llm_integration.py -q` — zero failures

## Documentation Impact
N/A: test-only fixture fix; no documented behavior change.

## Out of Scope
- `plans/done/20260908-221312_plan.md` (cfgval001)'s own fix — unrelated root cause.
- `issues/20260909-183426_toolcache01_removed-tool-result-caching-leaves-orphaned-config-keys-and-stale-references.md` —
  unrelated root cause, tracked separately.

## Dependencies
N/A: none. Discovered independently while investigating cfgval001's revalidation.

## Unresolved Questions
Whether a nonzero `progress_stagnation_window` value could itself cause
`_check_progress_stagnation()` to fire during either test's specific call sequence
(potentially masking the intended dedup/args assertion behind a different guard message)
— confirm `_check_progress_stagnation()`'s full trigger condition before picking a value,
rather than assuming any nonzero value is safe.

## AI Implementation Instruction
Add only the missing mock field to `_make_guard_ctx()`. Read
`_check_progress_stagnation()`'s full body first to choose a value that does not
interfere with either test's intended dedup/args-differentiation assertion.

## Traceability
- **Workflow phase**: N/A: manually filed
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260909-183549
- **Related target files**: see Target Files or Areas above
