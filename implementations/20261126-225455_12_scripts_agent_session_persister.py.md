## Goal

Mask SQLite error messages before they are logged or written as a user-facing warning (REQ-004 —
SQLite failure detail stays masked).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Two sites emit raw exception text: the `logger.debug` at line 333 and the user-facing
  `self._view.write_warning` at line 334; the close-failure warning at lines 204-206 logs the raw
  exception too. The user-facing warning is the site that also crosses into REQ-005 (normal CLI
  output), so it must be masked as well, not only the log line.
- No overlap with a sibling Plan on this file.

## Design decisions

- Reuse `format_sqlite_error` from `scripts/agent/wal_checkpoint_manager.py` (document 11) rather
  than defining a second formatter, so both modules share one type-plus-masked-message rule.
- The user-facing warning keeps its readable shape (`Diagnostics could not be saved: {type}: {masked}`)
  so the operator can still tell that the save failed.

## Alternatives considered

- Suppressing the user-facing warning entirely — rejected: the warning is the operator's signal that
  diagnostics were not persisted; only its content changes.

## Implementation
### Target file
`scripts/agent/session_persister.py`
### Procedure
- Route the exception text at lines 204-206, 333, and 334 through `format_sqlite_error` (document 11).

### Method
- `logger.warning("Failed to close workflow StateStore for session %s: %s", session_id,
  format_sqlite_error(exc))`; `logger.debug("DiagnosticStore.save failed: %s",
  format_sqlite_error(e))`; `self._view.write_warning(f"Diagnostics could not be saved:
  {format_sqlite_error(e)}")`.

### Details
- `OSError` is not a `sqlite3.Error`; the formatter accepts `BaseException` and returns the type name
  plus the masked message, so the `OSError` branch is covered by the same call.

### Companion test files
- `tests/agent/test_session_persister.py`
  - Procedure: assert the captured log records and the captured warning text contain the error type
    name and a masked message, with no absolute database path.
  - Validation: `uv run pytest tests/agent/test_session_persister.py`.

## Compatibility considerations

- Existing tests that compare the warning text must be updated to the masked form; the warning is
  still emitted on the same conditions.

## Security considerations

- AC-2 boundary for logs and AC-1 for the user-facing warning.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/test_session_persister.py`.
- Sequence: format → lint → type → arch → security.

## Completion criteria

- A `sqlite3.Error` with a credential- or path-bearing message produces masked output in both the log
  record and the user-facing warning.

## Out of Scope

- The shared formatter itself (document 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | companion `tests/agent/test_session_persister.py` |
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
- **Requirement ID**: `REQ-004` (SQLite error details reduced to type plus masked message)
- **Source issue**: `issues/20261119-145307_cliplc009_redaction-stderr-diagnostics.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-210258_cliplc009_redaction-stderr-diagnostics.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-225455
- **Related target files**: `scripts/agent/session_persister.py`, `tests/agent/test_session_persister.py`
