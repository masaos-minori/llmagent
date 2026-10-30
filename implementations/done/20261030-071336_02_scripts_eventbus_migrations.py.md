## Goal
Create the `eventbus.sqlite` migration registry `scripts/eventbus/migrations.py` (new): the domain-specific home where future EventBus version steps register, built on the shared framework (REQ-001 migration framework, REQ-009 registered paths preserve rows).

## Scope
- In scope: registry construction for the `eventbus` domain — a `REGISTRY` (new) collection of `MigrationSpec` entries from row 01's framework, and a ledger-bootstrap step (new) that adds the `schema_migrations` table and stamps the new baseline `PRAGMA user_version` on an existing version-3 database (mirrors the unstamped-database stamping logic in `scripts/eventbus/schema.py:90-92`).
- Out of scope: any forward content step such as `dlq_outbox` — `plans/20261029-221254_dlqbox001_dlq-sqlite-outbox.md` registers it after this Plan lands (sequenced dependency, confirmed in that Plan's Dependencies).

## Assumptions
- `eventbus` may import `scripts/shared/` but never `scripts/db/` (`.importlinter` `eventbus-is-isolated`); this module imports only `shared.db_migrations` and stdlib.
- Domain backup verification for the gate is supplied here as a callable that checks domain identity on the backup copy: required tables (`events`, `consumer_delivery`, `consumer_offsets`) present with expected columns, so no `db`-layer import is needed. It must not call `assert_matches` on a pre-migration copy: `assert_matches` compares against the current `scripts/eventbus/schema.sql` shape, which carries the ledger table once row 04 lands, and can never pass against a version-3 copy. `assert_matches` (verified present) is used only as the step postcondition, against the migrated shape.
- Baseline versions: current baseline is `PRAGMA user_version = 3` (`scripts/eventbus/schema.sql:45`); after the ledger DDL lands (row 04) the baseline becomes 4, so this registry's bootstrap step is `3 → 4`.

## Design decisions
- Registry is a module-level ordered mapping consumed by both startup wiring (row 03) and the CLI (row 05); registration order, not insertion side effects, defines the path.
- The bootstrap step is itself a registered, gate-gated migration (Plan Risk: ledger stamping is a schema mutation and runs through the same runner).

## Alternatives considered
- Placing the registry in `scripts/shared/` — rejected: domain registries stay in their own layer (Plan Design).

## Implementation
### Target file
- `scripts/eventbus/migrations.py` (new)

### Procedure
1. Import `MigrationSpec` from `shared.db_migrations`; define `REGISTRY` (new) as the ordered spec collection for this domain.
2. Register the bootstrap spec `eventbus_ledger_baseline` (new): precondition — `PRAGMA user_version` == 3 and the required tables are present in the pre-ledger shape (no `assert_matches`: it compares against the ledger-bearing canonical shape and cannot pass on a version-3 database); mutation — `CREATE TABLE IF NOT EXISTS schema_migrations` DDL (same contract as row 01) plus `PRAGMA user_version = 4`; postcondition — `assert_matches` passes against the ledger-bearing shape.
3. Export a `verify_backup(conn)` (new) helper implementing the injected backup-verification callable described in row 01 (integrity is done by the runner; here: domain identity via required-table presence and expected columns, valid on both pre-ledger and ledger-bearing shapes; `assert_matches` is not part of the gate verifier — see Assumptions).

### Method
New module only. SQL text mirrors the ledger DDL row that lands in `scripts/eventbus/schema.sql` (row 04) so baseline and step produce identical shape (fingerprint equivalence is checked by `tests/db/test_eventbus_schema_equivalence.py`). Introduce row 04's baseline bump in the same commit as this registry (DDL first), as the Plan's Phase 2 step orders them.

### Details
- `MigrationSpec` and `MigrationRunner` are created by row 01's procedure; this document assumes they exist when executed in `seq` order.
- No `dlq_outbox` or other content steps here.

## Compatibility considerations
- None for existing importers (new module). Import contract `eventbus-is-isolated` must stay KEPT.

## Security considerations
- Static SQL authored in-repo only; no user input paths.

## Rollback considerations
- Revert the commit; nothing references this module until rows 03/05 land.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_migrations.py` (row 15 writes these tests first).
- `lint-imports`; `uv run mypy --no-namespace-packages scripts/`.

## Completion criteria
- A version-3 EventBus database upgraded through this registry ends at version 4 with a `schema_migrations` row for `eventbus_ledger_baseline` and a passing fingerprint; an unregistered target (e.g. 5) is refused.

## Out of Scope
- EventBus startup wiring (row 03), CLI (row 05), outbox content step (dlqbox001).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261030-084500 | 20261030-084500 | Created scripts/eventbus/migrations.py: REGISTRY (eventbus_ledger_baseline 3->4 bootstrap), shared runner export, verify_backup (domain identity via required tables). Bumped schema.sql to v4 (ledger DDL) in same commit. |
| 2 | Add or update tests per Validation plan | Completed | 20261030-084500 | 20261030-084500 | Tests come from row 15's procedure document Wrote tests/eventbus/test_eventbus_migrations.py (10 tests): registry, forward path, apply+preserve+fingerprint, resume, unknown/downgrade refusal, gate, dry-run. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-084500 | 20261030-084500 | ruff+mypy(478)+lint-imports(6/6)+check_db_separation+check_docstrings clean; 1897 db/eventbus/shared + 24 deploy pass. Fixed stale /tmp v3 caches; made read_ledger tolerant of pre-ledger DBs; added schema_migrations to table inventory. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261030-084500 | 20261030-084500 | N/A for this row Updated test_eventbus_schema_version pinned-version test to v4 (schema.sql baseline bump). |

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
- **Requirement ID**: `REQ-001` (migration framework), `REQ-009` (registered paths preserve rows)
- **Source issue**: `issues/20261029-104500_dbmig001_forward-only-db-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-214108_dbmig001_forward-only-db-migrations.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-071336
- **Related target files**: `scripts/eventbus/migrations.py`