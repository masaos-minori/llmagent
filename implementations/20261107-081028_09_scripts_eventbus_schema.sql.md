## Goal

- Remove the `schema_migrations` CREATE TABLE from `scripts/eventbus/schema.sql` while keeping `PRAGMA user_version = 6`, so the canonical EventBus DDL is marker-free and the runtime fingerprint re-derives automatically (REQ-002: remove the EventBus ledger table; REQ-008: fingerprints regenerate from canonical DDL).

## Scope
**Release unit**: current-schema-only-cutover

- DDL deletion plus comment cleanup in this file only; `tests/deploy/test_init_db_eventbus_schema.py` needs no change (its expected fingerprint is derived from canonical `schema.sql` at runtime — Plan Assumptions).

## Assumptions

- `scripts/shared/eventbus_schema_fingerprint.py` computes the fingerprint from canonical `schema.sql` at runtime, so this deletion regenerates it with no manual fingerprint update (Plan Reference Files).

## Design decisions

- Keep `PRAGMA user_version = 6;` as the sole EventBus current-schema identifier (Issue line 34 via REQ-002).

## Alternatives considered

- Bumping `user_version` to 7 to mark the marker-free era: rejected — REQ-002/REQ-003 pin acceptance at 6 plus fingerprint; a bump would invalidate current-valid databases.

## Implementation
### Target file
`scripts/eventbus/schema.sql`

### Procedure
1. In the Phase 3 commit (Plan Phase 3), delete the ledger CREATE block and its introductory comments, keep the PRAGMA, and verify fingerprint-derived tests.

### Method
- Delete the comment lines introducing the ledger ("... New databases get this table here; existing databases receive it through the eventbus registry's bootstrap step.") (lines 44-45) and the `CREATE TABLE IF NOT EXISTS schema_migrations (id TEXT PRIMARY KEY, applied_at TEXT, ...)` statement (line 46 region; remove the complete statement including trailing columns).
- Adjust the PRAGMA comment block (lines 72-73: "Existing databases upgrade only through the eventbus registry's registered steps.") to state that databases stamped otherwise are refused and recreated — no registered-step language. Keep `PRAGMA user_version = 6;` (line 74) byte-identical.

### Details
- All other EventBus tables stay unchanged (REQ-006 preserves delivery/offset state).

## Compatibility considerations

- Databases carrying the old ledger (v6 + `schema_migrations`) fail the fingerprint gate by design and are recreated by the operator (Plan Design, persisted-schema checklist item 2).

## Security considerations

- N/A: DDL text deletion only.

## Rollback considerations

- Revert the commit restores the ledger DDL (single-commit change within the release unit).

## Validation plan

- `uv run pytest tests/deploy/test_init_db_eventbus_schema.py` — passes against the re-derived fingerprint (Plan row evidence: dynamic derivation).
- `uv run pytest tests/eventbus/` fingerprint tests + `uv run python tools/check_db_separation.py` — clean (AC-007).
- Whole-unit gates run in Plan Phase 5 per `rules/toolchain.md`.

## Completion criteria

- A fresh `eventbus.sqlite` created from this file has `user_version = 6` and no `schema_migrations` table (AC-002, AC-007).

## Out of Scope

- `_init_schema` gate rework — sibling document 07.
- EventBus docs row — own document (seq 29).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the ledger CREATE block and comments; keep `PRAGMA user_version = 6` (Plan Phase 3) | Pending | — | — | Release unit "current-schema-only-cutover" |
| 2 | Verify fingerprint-derived tests and `check_db_separation.py` | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) in the Phase 5 unit pass | Pending | — | — | |

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
- **Requirement ID**: REQ-002 (remove the EventBus ledger table, keep `user_version = 6`), REQ-008 (fingerprints regenerate from canonical DDL)
- **Source issue**: issues/20261106-125142_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-061846_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-081028
- **Related target files**: `scripts/eventbus/schema.sql`
