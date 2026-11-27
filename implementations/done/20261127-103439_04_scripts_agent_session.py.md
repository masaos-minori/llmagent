## Goal

Hold the degraded-session state on `AgentSession` and refuse a turn entry while the session is degraded, integrated with the existing generation model.

## Scope
**Release unit**: N/A: not part of a release unit

Requirement implemented: REQ-004 (degraded-session state and turn-entry refusal). Acceptance criterion: AC-3.

## Assumptions
- The degraded state is process-lifetime session state, not DB state: it is set by the turn boundary and read by the turn entry; nothing is written to the session DB.
- Clearing the state is out of scope: UNK-01 was resolved by user decision on 2026-11-27 as a defined seam, so this document provides the marking method and the read-only state check only.
- The state is not carried across a session transition: `switch_session` advances the generation (line 126), so a transition starts a fresh, non-degraded session; no transition snapshot field is added.

## Design decisions
- The flag lives on `AgentSession` (Plan decision D4) because it is the generation-model owner and the object the turn boundary already holds.
- The seam is a single clearing method with no criteria inside it: marking and reading are implemented here, the criteria stay in UNK-01's follow-up work item.

## Alternatives considered
- Keeping the flag on `TurnPersistence`: rejected, the boundary is per-turn while the degraded state must outlive the turn that caused it.

## Implementation
### Target file
`scripts/agent/session.py`

### Procedure
- Add a `degraded` boolean attribute to `AgentSession` alongside the existing state attributes (lines 58-60).
- Add a marking method called by the turn boundary when compensation fails.
- Add a read-only check the REPL turn entry uses to refuse a turn.
- Add the clearing seam method with no criteria; it only resets the flag.

### Method
- `mark_degraded()` (new) sets the flag; `is_degraded` (new) is a read-only property; `clear_degraded()` (new) is the seam body left empty of criteria.
- `turn_boundary` (line 233) refuses by raising before constructing the boundary when the flag is set, so a degraded session cannot start a turn. Exception type: `RuntimeError` (Step 3b correction, 20261127: the procedure did not name a type; `RuntimeError` matches the repository style, e.g. `SchemaMissingError` and the strict-mode guards).
- No change to `capture_target` / `is_current_target` (lines 95-104): the degraded flag is not part of `SessionTarget`, which stays an immutable identity pair.

### Details
- The flag is not included in the transition snapshot or in shutdown persistence, per the Assumptions above.
- `restore_identity` (line 128) does not clear the flag: restoring a session id does not make a degraded session healthy.

### Companion test files
- None: this row is not a companion of any code row; its coverage is the standalone test row for the REPL error handling, cited by two target rows.

## Compatibility considerations
- Session consumers across commands and REPL read the new property only; no existing signature changes.
- `docs/23_agent/agent_04_01_state-and-persistence-state-model.md` documents the behavior through the Plan's documentation row, not here.

## Security considerations
- N/A: no security-sensitive behavior.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Unit tests in `tests/agent/test_repl_error_handling.py`: marking, refusal, and the clearing seam.
- Static gates: `uv run ruff check`, `uv run mypy`.

## Completion criteria
- A degraded session cannot enter a turn (AC-3).
- The marking path and the clearing seam exist and are separately callable (AC-3).

## Out of Scope
- The degraded-state clearing criteria (UNK-01 seam).
- The REPL-side refusal message and display (`scripts/agent/repl_input_loop.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261127-112238 | files changed: scripts/agent/session.py |
| 2 | Add or update tests per Validation plan | Completed | — | 20261127-112238 | N/A: no test change needed; coverage via procedure 11; existing tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-112238 | 20261127-151312 | gates passed; full-suite run deferred to end of batch end-of-batch full suite: 16009 passed, 5 skipped; diff-cover 93% >= 90% |

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
- **Requirement ID**: REQ-004 (degraded-session state and turn-entry refusal)
- **Source issue**: `issues/20261119-145308_cliplc010_strict-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-211240_cliplc010_strict-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-103439
- **Related target files**: `scripts/agent/session.py`