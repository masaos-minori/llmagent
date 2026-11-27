## Goal

Refuse the next turn when the session is degraded and surface the compensation status distinctly in the REPL turn loop.

## Scope
**Release unit**: N/A: not part of a release unit

Requirement implemented: REQ-004 (degraded session cannot silently continue). Acceptance criterion: AC-3.

## Assumptions
- The degraded state is read from the session (`scripts/agent/session.py`, the row that owns the flag); this document only checks it at the turn entry.
- The display port is not modified: `scripts/agent/cli_view.py` and `scripts/agent/commands/output_port.py` are Reference Files, so the distinct surface uses the existing `write_turn_not_persisted` and `write_warning` methods.

## Design decisions
- The refusal happens before the turn boundary is created, so a degraded session never starts a write.
- The refusal is reported once per turn attempt through the existing warning path, matching the shutdown-refusal style at `_report_shutdown_refusal` (line 149).

## Alternatives considered
- Refusing inside the orchestrator: rejected, the REPL loop is the turn entry and already owns the per-turn error surface.

## Implementation
### Target file
`scripts/agent/repl_input_loop.py`

### Procedure
- Before dispatching a turn, check the session's degraded state and refuse the turn when it is set.
- In the persistence-error branch (lines 391-394), include the compensation status in the surfaced message.

### Method
- Add a refusal helper next to `_report_shutdown_refusal` that writes the degraded-session warning and returns `_TurnFlow.NEXT` without calling `handle_turn`.
- The existing `except ConversationPersistenceError` branch keeps `write_turn_not_persisted()`; the status is appended to the text it already prints.

### Details
- The check uses the session's degraded property, not a local flag, so the state survives across turns.
- The loop stays responsive after a refusal: the refusal path returns `_TurnFlow.NEXT` like the existing branches.

### Companion test files
- None: this row is not a companion of any code row; its coverage is the standalone test row for the REPL error handling, cited by two target rows.

## Compatibility considerations
- No display-port interface change; only message content changes.

## Security considerations
- N/A: no security-sensitive behavior.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Unit tests in `tests/agent/test_repl_error_handling.py`: degraded-session refusal and distinct display of compensation failure.
- Static gates: `uv run ruff check`, `uv run mypy`.

## Completion criteria
- A degraded session's next turn is refused with a distinct message (AC-3).
- The surfaced persistence message reports the compensation status (AC-3).

## Out of Scope
- Holding and clearing the degraded flag (`scripts/agent/session.py`).
- The display port itself (`scripts/agent/cli_view.py`, `scripts/agent/commands/output_port.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261127-114932 | files changed: scripts/agent/repl_input_loop.py (refusal helper + status in persistence branch) |
| 2 | Add or update tests per Validation plan | N/A | — | — | no companion test file for this row; coverage is procedure 11 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-114932 | 20261127-151312 | gates passed (ruff, mypy, bandit, module-size, mock-patch); full-suite run deferred to end of batch end-of-batch full suite: 16009 passed, 5 skipped; diff-cover 93% >= 90% |

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
- **Requirement ID**: REQ-004 (degraded session cannot silently continue)
- **Source issue**: `issues/20261119-145308_cliplc010_strict-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-211240_cliplc010_strict-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-103439
- **Related target files**: `scripts/agent/repl_input_loop.py`