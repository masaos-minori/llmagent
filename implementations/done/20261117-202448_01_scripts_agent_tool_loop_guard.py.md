## Goal

Make `ToolLoopGuard.check_dedup` honor the `<= 0` disables-the-guard convention that every
sibling guard in the class follows, so a zero or negative `tool_dedup_max_repeats` cleanly
disables dedup instead of blocking every tool call on its first occurrence (`REQ-001`,
`REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit

### Companion test files
- `tests/agent/test_tool_loop_guard.py`
  - Procedure: add a `TestCheckDedup` case asserting `check_dedup` returns `None` and leaves
    `seen_calls` empty when `tool_dedup_max_repeats` is `0` (and/or negative), and a case
    confirming detection is unchanged for a positive value.
  - Validation: `uv run pytest tests/agent/test_tool_loop_guard.py`.

## Assumptions
- The fix is behavior-preserving for the current config space (`tool_dedup_max_repeats >= 1`):
  the enabled path behaves exactly as before.
- Config validation (`validate_tool_dedup_max_repeats`, `>= 1`) stays unchanged, so the new
  guard is dead-code protection against a loosened validation, a programmatic/test
  invocation, or a future refactor.

## Design decisions
- Add `if ctx.cfg.tool.tool_dedup_max_repeats <= 0: return None` at the very top of
  `check_dedup`, before the `_iter_tool_call_keys` loop, mirroring the sibling guards.
- Preserve the increment-and-compare logic for the enabled case byte-for-byte.

## Alternatives considered
- Placing the guard after the first iteration: rejected — it would still mutate
  `seen_calls` for the disabled case; the guard must short-circuit before the loop so
  `seen_calls` is never touched when disabled.
- Changing `validate_tool_dedup_max_repeats` to allow `<= 0`: rejected — out of scope; the
  `>= 1` enforcement stays and the guard is purely defensive.

## Implementation
### Target file
- `scripts/agent/tool_loop_guard.py`

### Procedure
At the top of `check_dedup` (`scripts/agent/tool_loop_guard.py`, lines 415-434), before the
`for func, key in self._iter_tool_call_keys(message):` loop, add:
```python
if ctx.cfg.tool.tool_dedup_max_repeats <= 0:
    return None
```
Leave the increment-and-compare body (lines 422-434) verbatim.

### Method
- Locate `check_dedup` (line 415) and confirm the sibling guards gate on `<= 0`:
  `check_retry` (line 451), `check_cycle` (line 339), `check_error_limit` (lines 502-505),
  `scan_empty_result_repeat` (line 227), `scan_unavailable_repeat` (line 275),
  `record_tool_result` (line 214), `_check_progress_stagnation` (line 375).
- Insert the guard immediately after `ctx = self._ctx` (line 421) and before the loop.
- Confirm `ctx.cfg.tool.tool_dedup_max_repeats` is the correct config accessor (match the
  enabled-path read at line 424).

### Details
- Today `check_dedup` increments `seen_calls[key]` and compares
  `seen_calls[key] >= ctx.cfg.tool.tool_dedup_max_repeats` with no `<= 0` short-circuit.
  When the limit is `0` or negative, the comparison is always true, so the first occurrence
  of any `(tool, args)` pair is reported as a duplicate and the turn exits. The guard makes
  the disable uniform with the rest of the class.
- Existing `TestCheckDedup.test_window_zero_disabled_by_default` tests only the first call at
  the default value 3, not the `<= 0` disable; extend `TestCheckDedup` with an explicit
  `<= 0` case and a positive-value unchanged-detection case.

## Compatibility considerations
- Behavior is unchanged for every `tool_dedup_max_repeats >= 1` (the only value config
  validation currently permits); only the previously-impossible `<= 0` values gain a clean
  disable. No public or runtime-facing interface change.

## Security considerations
- N/A: no security impact; the guard only adds an off-ramp for config values that are
  otherwise forbidden by validation.

## Rollback considerations
- N/A: revert the commit; the single early-return is isolated.

## Validation plan
- Unit: drive `check_dedup` with `tool_dedup_max_repeats=0` (returns `None`, `seen_calls`
  empty) and a positive value (detection unchanged).
- Static: `uv run ruff check scripts/agent/tool_loop_guard.py` and
  `uv run mypy --no-namespace-packages scripts/agent/tool_loop_guard.py`.
- Suite: `uv run pytest tests/agent/test_tool_loop_guard.py`.

## Completion criteria
- `check_dedup` returns `None` without touching `seen_calls` when
  `tool_dedup_max_repeats <= 0` (`AC-001`).
- For any `tool_dedup_max_repeats >= 1`, dedup detection behaves exactly as before
  (`AC-002`).
- No tool call is blocked when the guard is disabled via a `<= 0` value (`AC-003`).
- New regression tests pass and existing tests still pass (`AC-004`).
- ruff and mypy are clean on the touched file.

## Out of Scope
- Any change to `check_retry`, `check_cycle`, `check_error_limit`,
  `scan_empty_result_repeat`, `scan_unavailable_repeat`, `record_tool_result`, or
  `report_effective_state`.
- Any change to config validation (`validate_tool_dedup_max_repeats`) or default values.
- Any change to the DAG scheduler, `execute_all_tool_calls`, or `LLMTurnRunner.run`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261117-212000 | 20261117-212200 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261117-212200 | 20261117-212300 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261117-212300 | 20261117-212500 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261117-212500 | 20261117-212530 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (`<= 0` early-return in `check_dedup`), `REQ-002` (enabled path unchanged), `REQ-003` (regression test)
- **Source issue**: `issues/20261117-181638_tlg002_dedup-disable-parity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261117-201452_tlg002_dedup-disable-parity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-202448
- **Related target files**: `scripts/agent/tool_loop_guard.py`, `tests/agent/test_tool_loop_guard.py`