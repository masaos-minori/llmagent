## Goal

Enable foreign-key enforcement on the MDQ DDL/fingerprint write path by switching
`create_production_tables()` to `write_mode=True` in
`scripts/mcp_servers/mdq/db_schema.py`. (`REQ-002` FK enforced on MDQ connections)

## Scope
**Release unit**: FK-ENFORCE

## Assumptions

- Same single-statement pragma delta as procedure 01 (`helper.py:39-54`); the shared
  helper remains the pragma owner.
- The cascade clause `ON DELETE CASCADE` (`db_schema.py:40`) is a safety net that no
  production delete path exercises today (plan P2); this change makes it enforced.

## Design decisions

- Switch the existing `write_mode` flag at `:122`; no MDQ-local `PRAGMA` statements.

## Alternatives considered

- **Leave DDL path at `write_mode=False`.** Rejected: DDL creates the FK-bearing
  tables; enforcement should hold on the same connection class that writes them.

## Implementation
### Target file
`scripts/mcp_servers/mdq/db_schema.py`

### Procedure
1. In `create_production_tables()` (`:112`, pragma call at `:121-123`), change
   `write_mode=False` to `write_mode=True` in the `apply_connection_pragmas(...)` call.

### Method
One-argument switch, mirroring procedure 01 so service and DDL paths are consistent.

### Details
Existing `test_db_schema.py` error-handling patches (fingerprint mismatch refusal)
are unaffected — they do not depend on FK state.

## Compatibility considerations

- Schema fingerprint comparison is pragma-independent; init_db / health paths keep
  working (`docs/41_db` claims unchanged).

## Security considerations

- Same write-time integrity guarantee as procedure 01.

## Rollback considerations

- Revert together with `mdq_service.py` (release unit FK-ENFORCE).

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_foreign_keys.py -q` (procedure 06) —
  `test_connection_pragma_foreign_keys_on (new)` asserts `PRAGMA foreign_keys` = 1 on a
  connection from `create_production_tables()` (AC-1).
- `uv run pytest tests/mcp_servers/mdq/ -m "not integration and not production_paths_allowed and not repo_scan" -q`.

## Completion criteria

- `PRAGMA foreign_keys` returns 1 on a connection produced by
  `create_production_tables()` (AC-1); existing schema-gate tests pass.

## Out of Scope

- Table DDL changes (the FK clause already exists at `:40`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Switch `write_mode` to True in `create_production_tables()` | Pending | — | — | |
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
- **Requirement ID**: `REQ-002` (MDQ connections enforce foreign keys)
- **Source issue**: issues/done/20261117-123019_adrchk019_mdq-workflow-db-settings.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-155712_adrchk019_mdq-workflow-db-settings.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-162732
- **Related target files**: `scripts/mcp_servers/mdq/db_schema.py`
