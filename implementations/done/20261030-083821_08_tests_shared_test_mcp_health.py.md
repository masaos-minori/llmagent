# Implementation Procedure: test_mcp_health.py reason-code and retry_after tests

## Goal

Cover the normalized reason constants and `retry_after_seconds` (new) derivation in
`tests/shared/test_mcp_health.py` (REQ-001).

## Scope

**In scope:**
- `tests/shared/test_mcp_health.py`: new test class for the row 02 additions.

**Out of scope:**
- Existing state-transition classes (characterization: untouched, must stay green).

## Assumptions
- Verified at HEAD `124e340b4`: file exists with classes `TestFailureThresholdAndReset`,
  `TestHalfOpenCooldownAndTrialDispatch`, `TestHalfOpenTrialOutcomes` built on
  `McpServerHealthRegistry` directly (no mocks beyond `time`). Test-first: new tests fail
  until row 02 lands.

## Design decisions
- New class `TestRetryAfterDerivation` (new):
  - boundary: cooldown 30.0s, failure drives UNAVAILABLE; with `time.monotonic`
    monkeypatched, `retry_after_seconds` (new) is `ceil(remaining)` just before expiry and
    `0` at/after expiry (never negative).
  - state mapping: HEALTHY/DEGRADED/unknown key → `None`; HALF_OPEN → `None` (trial
    window open); UNAVAILABLE → non-negative int.
  - purity: calling `cooldown_remaining` (new)/`retry_after_seconds` (new) repeatedly leaves
    `_states`, `_failure_counts`, `_unavailable_since`, `_half_open_trials` unchanged —
    the explicit guard against accidentally reusing `is_unavailable()`'s side effects.
  - reason constants: the two module constants equal the row 01 `Literal` values
    (`server_unavailable`, `half_open_trial_in_progress` (new)).

## Alternatives considered
- Freezing wall-clock via `time.sleep` boundaries: rejected — the suite already patches
  monotonic time patterns; sleeps add flakiness.

## Implementation
### Target file
`tests/shared/test_mcp_health.py`

### Procedure
1. Keep all existing classes byte-identical.
2. Append `TestRetryAfterDerivation` (new) with the cases above.

### Method
- Direct registry construction with explicit `failure_threshold`/
  `half_open_cooldown_sec`; `monkeypatch.setattr("time.monotonic", fake)` for boundaries.

### Details
- Use `math.ceil` expectations explicitly in assertions to pin rounding.

## Compatibility considerations
- No changes to existing assertions; no shared fixtures introduced.

## Security considerations
- Not applicable (test-only).

## Rollback considerations
- Delete the appended class to revert.

## Validation plan
- `uv run pytest tests/shared/test_mcp_health.py -v` — new class fails before row 02,
  green after; existing classes green at every step.

## Completion criteria
- Boundary, state-mapping, purity, and constant-equality tests pass after row 02;
  pre-existing classes unchanged.

## Out of Scope
- Row 02 implementation, invoker attachment tests (row 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append `TestRetryAfterDerivation` (new) (fails before row 02 lands) | Completed | 20261030-203916 | 20261030-203916 |  |
| 2 | Confirm existing state-machine classes byte-identical and green | Completed | — | 20261030-203916 |  |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/20261029-104507_toolhint001_dynamic-tool-health-hints.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-215111_toolhint001_dynamic-tool-health-hints.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-083821
- **Related target files**: `tests/shared/test_mcp_health.py`