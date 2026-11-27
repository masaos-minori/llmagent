## Goal

Record the compensation status from the persistence error in the orchestrator's persistence-error branch, so the turn result carries it.

## Scope
**Release unit**: N/A: not part of a release unit

Requirement implemented: REQ-003 (compensation status recorded on the turn result). Acceptance criterion: AC-2.

## Assumptions
- The branch keeps its existing `error_kind = "persistence"` behavior and re-raise; only the status is added.
- The status value comes from `ConversationPersistenceError.compensation` defined in `scripts/agent/turn_persistence.py`.

## Design decisions
- The status is read from the error object rather than recomputed in the branch, so the orchestrator stays a reporter, not an owner of compensation state.

## Alternatives considered
- N/A: the branch already owns the error; no alternative placement is needed.

## Implementation
### Target file
`scripts/agent/orchestrator.py`

### Procedure
- In the `except ConversationPersistenceError` branch (lines 202-211), read `exc.compensation` and pass it to the turn result.

### Method
- Bind the exception (`except ConversationPersistenceError as exc`) and record the status alongside `error_kind` at line 208.
- Keep `had_partial_text` and `was_compensated` unchanged: the branch still reports nothing persisted.

### Details
- The branch re-raises at line 211; the recorded status must be captured before the re-raise so the display path can read it.

### Companion test files
- `tests/agent/test_orchestrator.py`
  - Procedure: assert the persistence branch records the status from the error together with `error_kind`.
  - Validation: `uv run pytest tests/agent/test_orchestrator.py`.

## Compatibility considerations
- Display consumers read the status through the existing turn-result field; no interface change.

## Security considerations
- N/A: no security-sensitive behavior.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Unit test: `error_kind` plus compensation status surfaced from the branch.
- Static gates: `uv run ruff check`, `uv run mypy`.

## Completion criteria
- A persistence error reaching the orchestrator carries its compensation status into the turn result (AC-2).

## Out of Scope
- Defining the status enum (`scripts/agent/turn_persistence.py`).
- The REPL display of the status (`scripts/agent/repl_input_loop.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-003 (compensation status recorded on the turn result)
- **Source issue**: `issues/20261119-145308_cliplc010_strict-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-211240_cliplc010_strict-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-103439
- **Related target files**: `scripts/agent/orchestrator.py`, `tests/agent/test_orchestrator.py`
