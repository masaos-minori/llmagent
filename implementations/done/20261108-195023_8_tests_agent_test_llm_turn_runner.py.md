## Goal
Keep the runner-level unavailable-repeat bound tests passing after the guard is repointed (REQ-002; fallout row added by Plan amendment).

## Scope
**Release unit**: N/A: not part of a release unit
- `TestUnavailableRepeatBoundIntegration._real_guard_runner` in `tests/agent/test_llm_turn_runner.py`.

## Assumptions
- Fallout amendment (Plan, 2026-11-08): this file was not in the original target list; `_real_guard_runner` arms the real guard through the old knob, and three tests (bound terminates turn, tool definitions identical, default-off) depend on it.
- Depends on seq 3 of this Plan.

## Design decisions
- Change only the knob `_real_guard_runner` sets; the `limit` parameter keeps its meaning.

## Alternatives considered
N/A: a one-line repoint.

## Implementation
### Target file
`tests/agent/test_llm_turn_runner.py`

### Procedure
1. In `_real_guard_runner`, replace `ctx.cfg.tool.tool_empty_result_max_repeats = limit` with `ctx.cfg.tool.tool_unavailable_repeat_max_repeats = limit`.
2. In `test_default_off_runs_unbounded_scenario_as_today` update the comment to name `tool_unavailable_repeat_max_repeats=0`.

### Method
Two edits in the class; assertions stay unchanged.

### Details
- Other `tool_empty_result_max_repeats` assignments in this file (the `= 0` line in an unrelated test) are for the empty-result guard and stay.
- Mock-guard tests (`check_unavailable_repeat.return_value = None`) are unaffected.
- Execution-time fallout found (2026-11-09), two MagicMock-ctx pins needed beyond the original two edits:
  - `TestUnavailableRepeatBoundIntegration._real_guard_runner`: after the repoint the old knob stays an auto-created MagicMock and `check_all`'s empty-result scan raised `TypeError: '<=' not supported between MagicMock and int`; pin `tool_empty_result_max_repeats = 0` explicitly.
  - `TestAllFailingRoundGuardReachable._guarded_runner` (real guard, not named by the original procedure): its "pin the thresholds" block must also pin `tool_unavailable_repeat_max_repeats = 0`, otherwise `check_unavailable_repeat` compares a MagicMock with 0.
  - Same fixture-level fallout outside this file: the shared ctx helpers `tests/agent/test_orchestrator.py` (line 124) and `tests/integration/test_orchestrator_integration.py` (line 46) each pin the old knob to 0 and needed `tool_unavailable_repeat_max_repeats = 0` added alongside.

## Compatibility considerations
Tests only.

## Security considerations
N/A: tests only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_llm_turn_runner.py -q -k UnavailableRepeatBoundIntegration`

## Completion criteria
- The three tests pass; the bound test fails if the guard read the old knob.

## Out of Scope
Production code; other test files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Repoint `_real_guard_runner` and fix the comment | Completed | 2026-11-09 | 2026-11-09 | Plus execution-time fallout pins (see Details) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-09 | 2026-11-09 | Cycle B full-suite run: 11982 passed, diff-cover 100% |

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
- **Requirement ID**: `REQ-002` (runner tests follow the repointed guard)
- **Source issue**: `issues/20261107-191650_loopguard02_unavailable-repeat-coupling.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-190626_loopguard02_unavailable-repeat-coupling.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-195023
- **Related target files**: `tests/agent/test_llm_turn_runner.py`