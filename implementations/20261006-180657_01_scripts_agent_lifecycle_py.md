# Implementation Procedure: `scripts/agent/lifecycle.py` (add same-state STOPPED→STOPPED to `_VALID_TRANSITIONS`)

## Goal

Add `LifecycleState.STOPPED` to the valid targets of `LifecycleState.STOPPED` in `_VALID_TRANSITIONS` in `scripts/agent/lifecycle.py`, so that same-state transitions (e.g., `STOPPED→STOPPED`) are accepted by the state machine and no spurious warning is logged during shutdown (REQ-001, REQ-002).

## Scope

Line 34 of `scripts/agent/lifecycle.py` only: the `frozenset` of `LifecycleState.STOPPED`'s valid targets gains `LifecycleState.STOPPED`. No other line, transition, or file changes.

## Assumptions

- Same-state transitions during shutdown are harmless; modeling them as valid makes the state machine reflect reality rather than warn on them.
- `uv`/Python version supports `frozenset({...})` literal as currently used (already the case on every line).

## Design decisions

- Additive single-token insertion into the existing `frozenset` on line 34. The set grows from `{STARTING, FAILED}` to `{STARTING, FAILED, STOPPED}`. This preserves the invariant that the state machine accurately reflects allowed transitions (the plan's preferred Option B) without altering any other transition.
- No change to `assert_valid_transition()` logic: it already reads `_VALID_TRANSITIONS` and raises for absent targets; allowing `STOPPED→STOPPED` simply means it no longer raises for that case.

## Alternatives considered

- **Suppress same-state transition warnings (Option A)**: rejected by the Plan — it changes semantics and would suppress warnings even for same-state transitions outside shutdown, potentially masking real issues. This procedure instead makes the transition valid.

## Implementation

### Target file

`scripts/agent/lifecycle.py`

### Procedure

1. Open `scripts/agent/lifecycle.py`.
2. At line 34, change:
   `LifecycleState.STOPPED: frozenset({LifecycleState.STARTING, LifecycleState.FAILED}),`
   to:
   `LifecycleState.STOPPED: frozenset({LifecycleState.STARTING, LifecycleState.FAILED, LifecycleState.STOPPED}),`
3. Leave every other line (including the other states' entries and `assert_valid_transition`) untouched.

### Method

Textual edit of the `frozenset` contents on line 34 only. Locate the entry with `rg -n 'LifecycleState.STOPPED: frozenset' scripts/agent/lifecycle.py` (expected: line 34), confirm it currently reads `{LifecycleState.STARTING, LifecycleState.FAILED}`, then insert `, LifecycleState.STOPPED` before the closing `})`. Do not modify the key, spacing, or other lines.

### Details

- Current line 34: `LifecycleState.STOPPED: frozenset({LifecycleState.STARTING, LifecycleState.FAILED}),` — `STOPPED→STOPPED` is absent from the valid set, so `assert_valid_transition(STOPPED, STOPPED)` raises, and `factory.py:219-226` logs the spurious warning during shutdown.
- After the edit, `STOPPED→STOPPED` is a legal target; the shutdown re-transition no longer raises, eliminating the noise while `STOPPED→<other invalid>` (e.g., `STOPPED→RUNNING`) still raises and still warns (REQ-002 preserved).
- `assert_valid_transition` (lifecycle.py:46-58) is unchanged; it derives behavior solely from `_VALID_TRANSITIONS`, so no call-site edit is required.

## Compatibility considerations

- The change is global: `STOPPED→STOPPED` becomes valid in every environment (dev and production), consistent with `security_audit.py:89-91` treating `"none"` as fatal regardless of environment. Since `"none"` is fatal everywhere, firejail/sandbox availability is a separate concern; here the effect is purely on the lifecycle state machine.
- No interface, signature, or public API change.

## Security considerations

- N/A: this does not alter security enforcement. It removes a misleading log line for a benign shutdown re-transition; it does not weaken any validation. Ensure legitimate invalid transitions (different source/target states) still warn (REQ-002) — verified via the unit test in `tests/agent/test_lifecycle.py`.

## Rollback considerations

- Revert line 34 to `frozenset({LifecycleState.STARTING, LifecycleState.FAILED})`. Fully reversible single-token removal; no state or schema touched.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/lifecycle.py` | Static — line 34 edited | `rg -n 'LifecycleState.STOPPED: frozenset' scripts/agent/lifecycle.py` | Line 34 includes `LifecycleState.STOPPED` in the set |
| `scripts/agent/lifecycle.py` | Integration — same-state not warned | trigger `STOPPED→STOPPED` (or `bash /opt/llm/start_agent.sh` + Ctrl+C) | No `invalid state transition … STOPPED → STOPPED` warning; shutdown completes normally (REQ-001, REQ-003) |
| `scripts/agent/lifecycle.py` | Integration — different-state invalid still warned | trigger e.g. `STOPPED→RUNNING` | Warning still produced for the different-state invalid transition (REQ-002) |

## Completion criteria

- Line 34 of `scripts/agent/lifecycle.py` reads `frozenset({LifecycleState.STARTING, LifecycleState.FAILED, LifecycleState.STOPPED})`.
- `STOPPED→STOPPED` no longer raises/warns; a different-source/target invalid transition still raises and warns.
- Shutdown completes without the spurious `STOPPED→STOPPED` message.

## Out of scope

- Any other line or transition in `scripts/agent/lifecycle.py`.
- Modifying `scripts/agent/factory.py` (read-only reference; no change needed — the state machine now accepts the transition).
- Adding new lifecycle states or changing non-same-state transition logic.
- Updating tests — covered by the separate procedure for `tests/agent/test_lifecycle.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `LifecycleState.STOPPED` to valid targets on line 34 of `_VALID_TRANSITIONS` | Pending | — | — | REQ-001, REQ-002 |
| 2 | Run the validation sequence (same-state silent; different-state invalid still warns) | Pending | — | — | REQ-001..REQ-003 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A: no docs reference the transition table | Pending | — | |

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
- **Requirement ID**: REQ-001 (same-state `STOPPED→STOPPED` no longer warns), REQ-002 (legitimate invalid transitions still warn)
- **Source issue**: `issues/20261005-182100_suppress_lifecycle_log_noise.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-113432_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-180657
- **Related target files**: `scripts/agent/lifecycle.py`
