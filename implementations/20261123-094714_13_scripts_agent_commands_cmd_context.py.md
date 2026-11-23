## Goal

Word /clear as an in-memory conversation history reset at the command layer and report an undo reload failure with a recovery hint (REQ-007 clear wording, REQ-008 undo failure reporting; AC-4).

## Scope
**Release unit**: N/A: not part of a release unit

Single-file change; row 31 is covered as this document's companion.

## Assumptions
- Current code verified: `_cmd_clear` prints the service result message and `_cmd_undo` prints either a block reason or a success count (`cmd_context.py:118-137`); neither mentions persisted rows or reload recovery.

## Design decisions
- `_cmd_undo` catches `UndoReloadError` (seq 07) and prints the deleted-row count plus the recovery hint to run /session load with the current session id (REQ-008 plan Design).
- `/clear` wording comes from the seq 06 result messages; this row only adapts any command-layer text it owns and keeps both messages using "in-memory conversation history".

## Alternatives considered
N/A: wording and hint are fixed by REQ-007/REQ-008.

## Implementation
### Target file
`scripts/agent/commands/cmd_context.py`
### Procedure
1. In `_cmd_undo`, add the `UndoReloadError` branch (lazy import, matching the existing pattern) printing the error and the recovery hint.
2. Verify `/clear` and `/clear new` output paths render the seq 06 messages unchanged.
### Method
One exception branch added to the existing undo handler; clear paths pass through service text.
### Details
N/A: none beyond the plan text.

### Companion test files
- `tests/agent/commands/test_agent_cmd_context.py`
  - Procedure: assert the /clear output wording matches the service messages and that an injected reload failure prints the count plus the /session load hint.
  - Validation: `uv run pytest tests/agent/commands/test_agent_cmd_context.py -q`.

## Compatibility considerations
- `/undo` output text changes only on the failure path.

## Security considerations
N/A: the hint carries ids and a count only.

## Rollback considerations
N/A: revert the commit (depends on seq 07).

## Validation plan
- `uv run pytest tests/agent/commands/test_agent_cmd_context.py -q`.

## Completion criteria
/clear output states the in-memory reset explicitly, and a failed undo reload is reported with a recovery hint instead of silent divergence (AC-4).

## Out of Scope
Service messages (seq 06), error type (seq 07), docs (seq 15).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261123-122902 | After seq 06, 07 Changed: scripts/agent/commands/cmd_context.py Reopened after procedure 33: _cmd_clear is async def, awaits clear_conversation, reports SessionTransitionRefusedError via write_validation_error (cmd_context.py) |
| 2 | Add or update tests per Validation plan (companion row 31) | Completed | — | 20261123-122902 | Tests written first per plan Phase 5 Changed: tests/agent/commands/test_agent_cmd_context.py. Undo recovery hint and clear wording tests Reopened: tests/agent/commands/test_agent_cmd_context.py updated for async _cmd_clear, service routing and refusal |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-122208 | 20261123-123430 | 3e clean (ruff, mypy 608 files, lint-imports, bandit -ll, module size, docstrings, suppression, compat shims, mock patch targets). Full suite 2 failed/13510 passed, failures in out-of-scope tests (see report); diff-cover 98% End-of-batch run passed: 13519 passed, 5 skipped; mypy 608 files clean; lint-imports 6 kept; diff-cover 98% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261123-122208 | Docs via seq 15 N/A: docs handled by procedures 15-20 |

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
- **Requirement ID**: `REQ-007` (clear wording), `REQ-008` (undo failure message with hint)
- **Source issue**: `issues/20261119-145300_cliplc002_session-transition-generation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-232757_cliplc002_session-transition-generation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-094714
- **Related target files**: `scripts/agent/commands/cmd_context.py`, `tests/agent/commands/test_agent_cmd_context.py`