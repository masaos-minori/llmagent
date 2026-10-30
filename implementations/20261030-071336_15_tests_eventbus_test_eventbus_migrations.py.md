# Implementation Procedure: `tests/eventbus/test_eventbus_migrations.py` (eventbus registry + CLI tests)

## Goal
Create coverage for the eventbus migration registry and CLI including fault injection between backup and migration (Plan row 15; REQ-002, REQ-003, REQ-009).

## Scope
- In scope: `scripts/eventbus/migrations.py` (row 02), `scripts/eventbus/migrate.py` (row 05) against file-based eventbus-shaped fixtures.
- Out of scope: startup-path behavior (row 16), framework internals (row 14).

## Assumptions
- Fixtures build eventbus DBs by executing `scripts/eventbus/schema.sql` (the canonical shape source) into tmp_path files, so fixtures stay in lockstep with row 04's ledger DDL addition.
- CLI invoked via subprocess argv (`uv run python scripts/eventbus/migrate.py ...`) consistent with existing eventbus CLI test style; port-guard refusal is tested by binding a listener socket on 8015 in the test process, not by touching production services.

## Design decisions
- Registry tests exercise the shared framework through the real eventbus registry (no toy stubs) because AC-1 requires the actual baseline `3 → 4` path.
- Fault injection uses a registry-registered failing step function in a test-only chain on the fixture DB (the real registry is not mutated).

## Alternatives considered
- In-process CLI import instead of subprocess — rejected: exit-code classes (row 05 contract) are only observable at process boundary.

## Implementation
### Target file
- `tests/eventbus/test_eventbus_migrations.py` (new)

### Procedure
1. Fixtures: eventbus DB at `user_version=3` (pre-ledger shape, built from a snapshot of `schema.sql` without ledger DDL) and backup copies under tmp_path.
2. Tests:
   - Baseline migration: registered 3→4 on the pre-ledger fixture adds `schema_migrations`, writes the baseline row, stamps `user_version=4`, and preserves all event/delivery rows (REQ-009/AC-1: row counts before == after).
   - Postcondition: migrated fixture passes `scripts/shared/eventbus_schema_fingerprint.assert_matches` (fingerprint expectation updated per row 04).
   - Registry resolution: 4→4 no-op, 4→3 downgrade refusal, unknown-version refusal.
   - Fault injection between backup and migration: corrupt the backup copy after it is written (step-hook) → refusal before live mutation; live DB hash unchanged (REQ-002/AC-4).
   - CLI: `--dry-run` on a 3-version fixture leaves it byte-identical; `--apply` migrates and `--status` prints the ledger baseline row; listener on 8015 → apply refused with the service-holding exit class (row 05 contract).
3. Assert refusal messages name the ledger state (auditability).

### Method
pytest + tmp_path file fixtures + subprocess CLI invocations with argv lists (no shell strings, `rules/coding.md` subprocess rule).

### Details
- Fixtures execute the repo `scripts/eventbus/schema.sql` at test time instead of duplicating DDL inline.

## Compatibility considerations
- New file only. Cross-plan note: dlqbox001 (`plans/20261029-221254_dlqbox001_dlq-sqlite-outbox.md`) will add its own migration test after this Plan lands; this module must keep the baseline chain unique (`check_registered_migration_chain` green).

## Security considerations
- No production DB access; no secrets in fixtures.

## Rollback considerations
- Delete the file.

## Validation plan
- Automated: `uv run pytest tests/eventbus/test_eventbus_migrations.py` — fails before rows 02/04/05 land, passes after; included by `uv run pytest tests/eventbus`.
- Manual: none.

## Completion criteria
- Baseline migration preserves rows (AC-1); fault-injection refusal leaves live DB untouched (AC-4); CLI classes distinguished; fingerprint passes post-migration.

## Out of Scope
- Startup validation changes (row 16). Service restart drills (row 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Tests implemented in dbmig001 feature commit 5b301eecb; verified against current tree 2026-10-30. Baseline migration preserves rows, fault-injection refusal leaves live DB untouched, CLI classes distinguished, fingerprint passes post-migration, registry resolution (4->4 no-op, downgrade/unknown refusal), CLI dry-run/apply/status. |
| 2 | Add or update tests per Validation plan | Completed | — | — | Module tests/eventbus/test_eventbus_migrations.py: 10 tests pass. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff format OK; ruff check OK; mypy clean; pytest 10 passed. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | Out of scope: registry/CLI behavior (row 15), schema.sql (row 04). |

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
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-009`
- **Source issue**: `issues/20261029-104500_dbmig001_forward-only-db-migrations.md`
- **Source requirement**: N/A: no standalone requirement document exists
- **Source plan**: `plans/20261029-214108_dbmig001_forward-only-db-migrations.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Related target files**: `tests/eventbus/test_eventbus_migrations.py`
- **Generated at**: 20261030-071336