## Goal
Confirm at turn level that the unavailable-repeat guard is armed only by its own knob (REQ-006 additive wiring; REQ-005 independence through the runner).

## Scope
**Release unit**: N/A: not part of a release unit
- One small regression test in `tests/agent/test_tool_loop_guard_wiring.py`.

## Assumptions
- Adversarial finding: this file covers the empty-result guard at turn level and builds ctx directly (not through `_build_tool_config`); the builder-level REQ-006 check lives in `test_tool_loop_guard.py`. This row therefore adds only a runner-level independence check.
- `_ctx(max_repeats)` sets the old knob; the new test sets the new knob explicitly.

## Design decisions
- Add one test to `TestTurnLevelAcceptance` asserting that with `tool_empty_result_max_repeats = 3` and the new knob 0, hinted unavailable results never fail the turn with `unavailable_repeat`.

## Alternatives considered
N/A: smallest runner-level check that adds coverage beyond the unit matrix.

## Implementation
### Target file
`tests/agent/test_tool_loop_guard_wiring.py`

### Procedure
1. Add `test_old_knob_alone_does_not_arm_unavailable_repeat` (new) to `TestTurnLevelAcceptance`: build `_ctx(3)`, leave `tool_unavailable_repeat_max_repeats` (new) at 0, create the guard, call `guard.observe_availability` with a hinted result three times, and assert `guard.scan_unavailable_repeat() is None` and `guard.check_unavailable_repeat() is None`.

### Method
Import `ToolLoopGuard` the way neighbouring tests do; build the hinted `ToolCallResult` with the same fields `test_tool_loop_guard.py::_hinted_result` uses (copy the minimal helper locally, do not import across test modules).

### Details
- Existing tests in this file use only the empty-result knob and are unaffected.

## Compatibility considerations
Tests only.

## Security considerations
N/A: tests only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_tool_loop_guard_wiring.py -q`

## Completion criteria
- The new test passes with the repointed guard and fails if the guard still read the old knob.

## Out of Scope
Builder-level checks (`test_tool_loop_guard.py`), production code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the runner-level independence test | Completed | 2026-11-09 | 2026-11-09 |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-09 | 2026-11-09 |  |

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
- **Requirement ID**: `REQ-006` (additive wiring), `REQ-005` (independence at turn level)
- **Source issue**: `issues/20261107-191650_loopguard02_unavailable-repeat-coupling.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-190626_loopguard02_unavailable-repeat-coupling.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-195023
- **Related target files**: `tests/agent/test_tool_loop_guard_wiring.py`