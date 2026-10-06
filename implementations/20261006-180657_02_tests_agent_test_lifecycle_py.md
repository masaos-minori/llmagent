# Implementation Procedure: `tests/agent/test_lifecycle.py` (expect `STOPPED` in valid targets for `STOPPED→RUNNING`)

## Goal

Update `tests/agent/test_lifecycle.py::TestAssertValidTransition::test_invalid_transition_from_stopped_shows_targets` so it asserts that `STOPPED` appears in the valid-targets list of the error message, covering REQ-001 (same-state `STOPPED→STOPPED` is now a legal transition) after `scripts/agent/lifecycle.py` adds `LifecycleState.STOPPED` to its own valid targets.

## Scope

The single test method `test_invalid_transition_from_stopped_shows_targets` (lines 670-677) in `tests/agent/test_lifecycle.py`: add one assertion (`assert "STOPPED" in msg`). No other test or file changes.

## Assumptions

- After the `lifecycle.py` change, `assert_valid_transition(LifecycleState.STOPPED, LifecycleState.RUNNING)` still raises (RUNNING is not a valid target of STOPPED), and the raised message lists all valid targets of STOPPED, now including `STOPPED`.
- The message format is unchanged (still `... Valid targets from {from_state}: {targets_str}`), so substring assertions remain valid.

## Design decisions

- Additive assertion only: append `assert "STOPPED" in msg` alongside the existing `assert "STARTING" in msg` / `assert "FAILED" in msg`. The existing assertions keep passing because STARTING and FAILED remain valid targets of STOPPED.
- The test continues to exercise a genuinely-invalid transition (`STOPPED→RUNNING`) so it still validates the warning path; asserting `STOPPED` in the listed targets proves the state machine now recognizes same-state as valid.

## Alternatives considered

- **Rewrite the test to assert `STOPPED→STOPPED` does not raise**: rejected — that belongs to a different test; this method's contract is "invalid transition shows valid targets." Keep its contract and strengthen it with the `STOPPED` assertion.

## Implementation

### Target file

`tests/agent/test_lifecycle.py`

### Procedure

1. Open `tests/agent/test_lifecycle.py`.
2. In `test_invalid_transition_from_stopped_shows_targets` (lines 670-677), add an assertion that `STOPPED` is in the message. Change:
   ```python
       def test_invalid_transition_from_stopped_shows_targets(self) -> None:
           with pytest.raises(ValueError) as exc_info:
               assert_valid_transition(LifecycleState.STOPPED, LifecycleState.RUNNING)
           msg = str(exc_info.value)
           assert "Invalid lifecycle transition" in msg
           assert "Valid targets from" in msg
           assert "STARTING" in msg
           assert "FAILED" in msg
   ```
   to:
   ```python
       def test_invalid_transition_from_stopped_shows_targets(self) -> None:
           with pytest.raises(ValueError) as exc_info:
               assert_valid_transition(LifecycleState.STOPPED, LifecycleState.RUNNING)
           msg = str(exc_info.value)
           assert "Invalid lifecycle transition" in msg
           assert "Valid targets from" in msg
           assert "STARTING" in msg
           assert "FAILED" in msg
           assert "STOPPED" in msg
   ```
3. Leave every other test (including `test_invalid_transition_from_failed_shows_targets`, `test_valid_transition_does_not_raise`, `test_transition_from_unknown_never_raises`) untouched.

### Method

Locate the method with `rg -n 'def test_invalid_transition_from_stopped_shows_targets' tests/agent/test_lifecycle.py` (expected: line 670), confirm the current assertions (lines 674-677), then insert the `assert "STOPPED" in msg` line after `assert "FAILED" in msg` (line 677). Do not alter the `pytest.raises` block or other methods.

### Details

- Current lines 670-677 assert `STARTING` and `FAILED` are listed as valid targets of STOPPED. After the `lifecycle.py` edit, `STOPPED` is also listed, so `assert "STOPPED" in msg` passes and actively verifies REQ-001.
- The `with pytest.raises(ValueError)` guard remains valid because `STOPPED→RUNNING` is still an illegal transition (RUNNING ∉ valid targets of STOPPED).

## Compatibility considerations

- N/A: no production-code compatibility impact; this is a test-only change reflecting the `_VALID_TRANSITIONS` update.

## Security considerations

- N/A: test-only change. It preserves coverage that legitimate invalid transitions still warn (REQ-002) by keeping the `pytest.raises` assertion intact.

## Rollback considerations

- Remove the added `assert "STOPPED" in msg` line. Fully reversible; no other state affected.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_lifecycle.py` | Unit — transition suite | `uv run pytest tests/agent/test_lifecycle.py::TestAssertValidTransition` | All transition tests pass, including `test_invalid_transition_from_stopped_shows_targets` (REQ-002) |

## Completion criteria

- `test_invalid_transition_from_stopped_shows_targets` contains `assert "STOPPED" in msg`.
- `uv run pytest tests/agent/test_lifecycle.py::TestAssertValidTransition` passes.

## Out of scope

- Any method other than `test_invalid_transition_from_stopped_shows_targets`.
- Modifying `scripts/agent/lifecycle.py` — covered by the separate procedure for that file.
- Adding new test classes or covering other requirements beyond REQ-001/REQ-002.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `assert "STOPPED" in msg` to `test_invalid_transition_from_stopped_shows_targets` (lines 670-677) | Pending | — | — | REQ-001, REQ-002 |
| 2 | Run `uv run pytest tests/agent/test_lifecycle.py::TestAssertValidTransition` | Pending | — | — | REQ-002 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A: no docs reference the test | Pending | — | |

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
- **Requirement ID**: REQ-001 (same-state `STOPPED→STOPPED` now valid, verified via the strengthened assertion), REQ-002 (different-state invalid transitions still warn)
- **Source issue**: `issues/20261005-182100_suppress_lifecycle_log_noise.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-113432_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-180657
- **Related target files**: `tests/agent/test_lifecycle.py`
