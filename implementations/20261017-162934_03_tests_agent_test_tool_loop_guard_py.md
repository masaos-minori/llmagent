# Implementation Procedure — `tests/agent/test_tool_loop_guard.py`

## Goal

Add regression coverage for the startup diagnostic that reports the effective on/off state
of the retry-suppression and empty-result guards (`REQ-001`, `REQ-002`, `REQ-003`,
`REQ-004`).

## Scope

Modify only `tests/agent/test_tool_loop_guard.py`. Add:
- a test asserting `report_effective_state()` reflects the configured on/off state for both
  enabled and disabled configs (REQ-001);
- a test that repeated construction emits only once (module-flag behavior) (REQ-002);
- a test that a guard whose logger is unavailable does not raise on construction (REQ-003);
- a regression confirming defaults are unchanged (REQ-004);
- confirm existing gating tests (`test_retry_max_zero_disabled`, `test_window_zero_disabled`,
  `TestCheckAll`) still pass (REQ-007).
Depends on the code changes in `scripts/agent/tool_loop_guard.py` (row 1) and
`scripts/agent/config_dataclasses.py` (row 2).

## Assumptions

- The existing ~356-line suite covers gating semantics incl. `test_retry_max_zero_disabled`
  (line 166) and `TestCheckAll` (line 226).
- `report_effective_state()` returns a concise summary string containing
  `retry_suppression=<on|off>(<n>)` and `empty_result_detection=<on|off>(<n>)`.
- Construction calls `report_effective_state()` once per process via the module-once flag.

## Design decisions

- Build a `ToolLoopGuard` with a config where both guards are enabled and assert the summary
  reports `retry_suppression=on(...)` and `empty_result_detection=on(...)`.
- Build a config where empty-result detection is disabled (default) and assert
  `empty_result_detection=off(...)`.
- For the once-per-process assertion, construct the guard twice against different configs
  and assert the underlying logger was invoked only once (or that the module flag prevents
  a second emit).
- For the logging-unavailable case, set the guard's logger to a stub that raises and assert
  construction does not propagate.
- Assert defaults via `ToolConfig()` → `tool_error_retry_max == 1`,
  `tool_empty_result_max_repeats == 0` (REQ-004).

## Alternatives considered

- Constructing real `AgentContext` vs. a lightweight stub: reuse whatever fixture the
  existing suite uses for `ctx.cfg.tool`; keep consistent with neighboring tests.

## Implementation

### Target file

`tests/agent/test_tool_loop_guard.py`

### Procedure

1. Add `test_report_effective_state_on_off`:
   - Construct a guard with a config where both guards are enabled; assert the summary
     contains `retry_suppression=on(` and `empty_result_detection=on(`.
   - Construct a guard with empty-result detection disabled; assert
     `empty_result_detection=off(`.
2. Add `test_report_effective_state_emits_once_per_process`:
   - Construct the guard twice; assert the logger was called only once (module-flag
     behavior). If the suite cannot observe the module flag directly, assert the summary is
     produced by only one of the two constructions.
3. Add `test_report_effective_state_logger_unavailable_does_not_raise`:
   - Point the guard's logger at a stub that raises; construct the guard and assert no
     exception propagates (REQ-003).
4. Add/confirm a defaults regression: `ToolConfig().tool_error_retry_max == 1` and
   `ToolConfig().tool_empty_result_max_repeats == 0` (REQ-004).
5. Confirm existing `test_retry_max_zero_disabled`, `test_window_zero_disabled`,
   `TestCheckAll` still pass (REQ-007).

### Method

Append test functions; reuse existing fixtures/helpers.

### Details

- Align the once-per-process assertion with how row 1 implements the flag (module-level
  `_STARTUP_REPORTED`); if the flag is module-global, observe it via the logger call count.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A (observability property).

## Rollback considerations

Revert the commit to the test file.

## Validation plan

- Run the guard suite; all pass.
- Command: `uv run pytest tests/agent/test_tool_loop_guard.py -q`.

## Completion criteria

The diagnostic on/off test asserts correct summaries for enabled and disabled configs; the
once-per-process emit, logging-unavailable-safe, and defaults regressions pass; existing
gating tests remain green.

## Out of scope

`scripts/agent/tool_loop_guard.py` (separate row), `scripts/agent/config_dataclasses.py`
(separate row), the doc update (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the test changes in test_tool_loop_guard.py | Pending | — | — | align with rows 1–2 |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-001` (on/off diagnostic test), `REQ-002` (once per process),
  `REQ-003` (logging-unavailable safe), `REQ-004` (defaults unchanged), `REQ-007` (existing
  gating tests pass)
- **Source issue**: `issues/done/20261017-123510_retrysup01_make-retry-suppression-and-empty-result-defaults-observable.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-153234_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162934
- **Related target files**: `tests/agent/test_tool_loop_guard.py`
