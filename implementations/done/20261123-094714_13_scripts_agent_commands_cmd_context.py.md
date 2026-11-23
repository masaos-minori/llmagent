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
- Verification finding (2026-11-23): seq 06 made `clear_conversation` async, so `_cmd_clear` became `async def` and the `/clear` CommandDef in `command_defs_list.py` switched to `is_async=True` (the registry fail-fast check validates handler/flag agreement).

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-23 | 2026-11-23 | After seq 06, 07 _cmd_clear async; /clear CommandDef is_async=True; UndoReloadError branch with /session load hint |
| 2 | Add or update tests per Validation plan (companion row 31) | Completed | 2026-11-23 | 2026-11-23 | Tests written first per plan Phase 5 clear tests converted to async + reload-failure hint test (61 pass) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-23 | 2026-11-23 | ruff, mypy, lint-imports, targeted pytest pass incl. registry consistency test |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261123-120932 | 20261123-120932 | Batch 20261123-094714 executed 2026-11-23; all steps Completed; full gates pass |

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
