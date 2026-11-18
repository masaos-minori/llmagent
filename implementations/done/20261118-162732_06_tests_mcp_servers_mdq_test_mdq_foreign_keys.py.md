## Goal

Create `tests/mcp_servers/mdq/test_mdq_foreign_keys.py` — the test-first FK lock:
cascade-delete behavior, on-connection `PRAGMA foreign_keys` assertion, and
orphan-chunk insert rejection. (`REQ-001` test-first red-first evidence, `REQ-002`
FK enforcement locked by tests)

## Scope
**Release unit**: FK-ENFORCE

## Assumptions

- This document runs before procedures 01/02 in execution: the cascade test is
  required to be red first; record the failing assertion in the Plan Execution Status
  before Phase 2 (plan Validation plan: red-first evidence).
- `MdqService` can be built against a tmp `db_path` without network dependencies,
  following `tests/mcp_servers/mdq/test_index_delete.py`'s fixture pattern (plan
  Assumptions).

## Design decisions

- Build the service through the production write path (`write_document_chunks`) and
  the production connection factory (`_get_db_connection()`), not hand-rolled
  connections, so the test locks the real pragma shape.
- Raw `DELETE FROM documents` (bypassing `delete_file_from_index`) is intentional: it
  exercises the cascade clause (`db_schema.py:40`) no production path hits today.

## Alternatives considered

- **Extend `test_index_delete.py`.** Rejected: that file locks the ordered-delete
  behavior; FK enforcement needs a cascade path the ordered deletes never trigger.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_foreign_keys.py` (new)

### Procedure
1. `test_cascade_delete_removes_chunks (new)`: build `MdqService` on a tmp DB, insert
   document + chunks via the production write path, `DELETE FROM documents` only,
   assert `chunks` is empty. Must fail before procedures 01/02 land.
2. `test_connection_pragma_foreign_keys_on (new)`: `PRAGMA foreign_keys` returns 1 on
   a connection from `_get_db_connection()` and from `create_production_tables()`.
3. `test_orphan_chunk_insert_rejected (new)`: inserting a chunk with an unknown
   `doc_id` raises `sqlite3.IntegrityError`.

### Method
Reuse the fixture setup of `tests/mcp_servers/mdq/test_index_delete.py` (tmp `db_path`
service construction); keep tests deterministic (no time- or host-dependent state).

### Details
No production-code changes in this document; the red-first state is temporary and
resolved by procedures 01/02 in the same release unit.

## Compatibility considerations

- The file lands green in the FK-ENFORCE commit (after 01/02); red evidence lives in
  the Execution Status record, not in git history.

## Security considerations

- N/A: test-only file.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_foreign_keys.py -q` — red before
  procedures 01/02 (assertion failure recorded), green after (AC-1).
- `uv run ruff check tests/mcp_servers/mdq/test_mdq_foreign_keys.py`.

## Completion criteria

- All three tests green after FK-ENFORCE lands; the cascade test was demonstrably red
  before it (AC-1, red-first evidence recorded).

## Out of Scope

- `health_check.py` connection (deviation UNK-02; no assertion against it).
- Orphan data cleanup (report-only).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the three FK tests (red-first run recorded) | Completed | 2026-11-18 | — | red-first evidence 2026-11-18: cascade FAIL assert 1==0 (chunk survives raw documents DELETE); pragma FAIL assert 0==1; orphan-insert FAIL DID NOT RAISE IntegrityError (all 3 red before procedures 01/02) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-18 | 2026-11-18 |  |

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
- **Requirement ID**: `REQ-001` (test-first FK lock), `REQ-002` (FK enforcement tests)
- **Source issue**: issues/done/20261117-123019_adrchk019_mdq-workflow-db-settings.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-155712_adrchk019_mdq-workflow-db-settings.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-162732
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_foreign_keys.py`