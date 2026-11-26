## Goal

Reduce logged SQLite errors to the error type name plus a masked message (REQ-004 — internal logging
of SQLite failures carries no raw detail).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The logging sites reached from the `sqlite3.Error` handlers are lines 200-203 (PASSIVE failure) and
  242-245 (TRUNCATE retry); the handlers themselves are at 196 and 230. The Plan's earlier line
  numbers 196/230 name the handlers, not the log calls — corrected in Step 3a.
- Additional masked sites exist in the same module (lines 300, 318, 330, 342, 362); they are covered
  by the same helper, so this document applies the transformation through one shared formatter
  rather than editing each call.
- No overlap with a sibling Plan on this file.

## Design decisions

- Add one module-level formatter, `format_sqlite_error` (new), that returns
  `"{type(exc).__name__}: {masked message}"`; every logging site uses it (Plan D1, one redaction
  model).
- The error type name stays visible because the checkpoint policy decisions depend on distinguishing
  `sqlite3.OperationalError` from other `sqlite3.Error` subclasses.

## Alternatives considered

- Masking each call site inline — rejected: it duplicates the redaction rule across the module and
  drifts when new handlers are added.

## Implementation
### Target file
`scripts/agent/wal_checkpoint_manager.py`
### Procedure
- Add `format_sqlite_error` (new) and route every `sqlite3.Error` message through it before logging.

### Method
- `format_sqlite_error(exc)` returns `f"{type(exc).__name__}: {_mask_secrets(str(exc))}"`, with
  `redact_path` (document 01) applied to the message so a database file path becomes a logical
  identifier.
- Replace the `%s`-formatted exception arguments at the logging sites with the formatter's result.

### Details
- `_interrupted_error` and the returned error tuples keep their shape; only the message text they
  carry is produced through the formatter.

### Companion test files
- `tests/agent/test_wal_checkpoint_manager.py`
  - Procedure: assert the captured log records contain the error type name and a masked message, with
    no absolute database path.
  - Validation: `uv run pytest tests/agent/test_wal_checkpoint_manager.py`.

## Compatibility considerations

- Log text changes only; the checkpoint return contract and error tuples are unchanged.

## Security considerations

- AC-2 boundary: internal logs are the disclosure surface for SQLite error detail.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/test_wal_checkpoint_manager.py`.
- Sequence: format → lint → type → arch → security.

## Completion criteria

- A `sqlite3.Error` whose message contains a path or a credential produces a log line with the type
  name and a masked message only.

## Out of Scope

- Session-persistence logging (document 12).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | companion `tests/agent/test_wal_checkpoint_manager.py` |
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
- **Related target files**: `scripts/agent/wal_checkpoint_manager.py`, `tests/agent/test_wal_checkpoint_manager.py`
