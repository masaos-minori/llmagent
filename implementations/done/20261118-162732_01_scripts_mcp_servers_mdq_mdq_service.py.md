## Goal

Enable SQLite foreign-key enforcement on every MDQ service connection by switching
`_get_db_connection()` to `write_mode=True` in `scripts/mcp_servers/mdq/mdq_service.py`.
(`REQ-002` FK enforced on MDQ data connections)

## Scope
**Release unit**: FK-ENFORCE

## Assumptions

- `apply_connection_pragmas` (`scripts/db/helper.py`) stays the single pragma owner;
  `write_mode=True` changes exactly one executed statement per connection
  (`foreign_keys=ON`; WAL/synchronous/busy_timeout identical either way, `helper.py:39-54`).
- `health_check.py:157` keeps `write_mode=False` (read-only probe; plan UNK-02
  deviation) — not a target row, do not touch it.

## Design decisions

- Switch the existing `write_mode` flag instead of hand-writing `PRAGMA foreign_keys`
  in MDQ (plan Design: pragma ownership stays in the shared helper).

## Alternatives considered

- **MDQ-local `PRAGMA foreign_keys=ON` statements.** Rejected: duplicates pragma
  ownership and violates the single-owner design.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_service.py`

### Procedure
1. In `_get_db_connection()` (`:132-133`), change `write_mode=False` to
   `write_mode=True` in the `apply_connection_pragmas(...)` call.

### Method
One-argument switch; the same factory already serves reads and writes
(`indexer.py:103, 410`, `index_delete`, `index_write`, get/search paths), so no
call-site split is introduced.

### Details
`INSERT OR REPLACE INTO documents` (`index_write.py:75`) stays safe under FK because
the transaction deletes that document's chunks first (`index_write.py:73`); locked by
the sibling procedure 06 cascade test and existing `test_index_delete.py`.

## Compatibility considerations

- FK enforcement applies to new DML only; existing rows are not retroactively
  validated (measured orphans: 0).
- `tests/mcp_servers/mdq/` fixtures build services on tmp DBs through this factory —
  FK ON must not break existing behavior-lock tests (full-suite gate proves it).

## Security considerations

- Closes the guarantee gap that a chunk row can reference a nonexistent document
  (write-time integrity).

## Rollback considerations

- Reverting this file without reverting `db_schema.py` leaves DDL and DML paths
  inconsistent; revert the release unit as a whole.

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_foreign_keys.py -q` (procedure 06)
  — cascade test green only after this switch (AC-1).
- `uv run pytest tests/mcp_servers/mdq/ -m "not integration and not production_paths_allowed and not repo_scan" -q` — existing MDQ tests pass.
- `uv run ruff check scripts/mcp_servers/mdq/`, `uv run mypy scripts/mcp_servers/mdq/mdq_service.py`.

## Completion criteria

- `PRAGMA foreign_keys` returns 1 on a connection from `_get_db_connection()`;
  orphan-chunk `INSERT` raises `sqlite3.IntegrityError` (AC-1).

## Out of Scope

- `scripts/mcp_servers/mdq/health_check.py` (stays `write_mode=False`, UNK-02).
- Orphan cleanup (report-only per `REQ-008`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Switch `write_mode` to True in `_get_db_connection()` | Completed | 2026-11-18 | — |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-18 | 2026-11-18 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | `tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py` (not a plan target row) builds an orphan state by deleting a `documents` row and expects the chunks to survive; FK ON cascades and breaks it. Resolved by simulating the legacy/external orphan in that test with `PRAGMA foreign_keys=OFF` on the helper connection only | Yes | 2026-11-18 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (MDQ connections enforce foreign keys)
- **Source issue**: issues/done/20261117-123019_adrchk019_mdq-workflow-db-settings.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-155712_adrchk019_mdq-workflow-db-settings.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-162732
- **Related target files**: `scripts/mcp_servers/mdq/mdq_service.py`