## Goal
Move the control-message assertions to the `TurnControl` contract and cover directive construction.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The existing `_stale_row` helper (line 732) records a row and ages it; it must pass the new `args_hash`
  argument so the recorded row is matchable.

## Design decisions
- Assert the returned control's text separately from its directives, so the two contracts are tested
  independently.

## Alternatives considered
N/A: test-only change.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_engine.py`

### Procedure
Update the control-message tests and add directive-construction tests.

### Method
- Replace the `idempotency_key=` assertions with assertions that the text names tool and `args_hash` and contains
  no id (AC-004).
- Add tests that a `TurnControl` (resolved from sibling procedure seq 07) carries one directive for an
  `interrupted` replayable row, none for a `non_retryable` row, and none for an `outcome_unknown` row (AC-003).
- Keep the existing assertion that the row is classified `interrupted` exactly once.

### Details
- `_stale_row` gains an `args_hash` argument with a fixed test value so the directive hash is predictable.
- The no-listed-rows case still returns `None`; keep that test.

## Compatibility considerations
The store fixture must expose the reconstruction helper from sibling procedure seq 02; the tests call it through
the engine, not directly.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/workflow/test_workflow_engine.py` (AC-003, AC-004).

## Completion criteria
The assertions fail if the id reappears in the control text, and the directive tests fail if a non-retryable or
outcome-unknown row produces one.

## Out of Scope
No change to the workflow stage-execution tests in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update control-message assertions and add directive tests | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (no directive for non-retryable or outcome-unknown), `REQ-005` (control text carries no id)
- **Source issue**: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261125-105505_mcpai004_logical-idempotency-key-replay.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-112546
- **Related target files**: `tests/agent/workflow/test_workflow_engine.py`
