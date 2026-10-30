## Goal
Rework `_init_schema` in `scripts/eventbus/schema.py` so a registered forward migration path runs through the shared framework (gate-gated) at startup, while every unknown, cyclic, or downgrade case keeps today's fail-closed refusal (REQ-003 refusal semantics, REQ-005 fail-closed startup, REQ-009 registered paths preserve rows).

## Scope
- In scope: startup path only — `_init_schema` (`scripts/eventbus/schema.py:68-96`) consults `scripts/eventbus/migrations.py::REGISTRY` via the row-01 runner instead of refusing a lower version outright.
- Out of scope: registry content (row 02), CLI (row 05), baseline DDL (row 04).

## Assumptions
- Migration at startup runs inside service init before the service serves traffic, holding the same connection; the CLI path refuses while the EventBus service (port 8015) runs (Plan Risk). Needs confirmation: none — semantics fixed by the Plan.
- Preserved today's behaviors: absent schema → create from schema.sql; `found == expected` → fingerprint check; unstamped (`user_version 0`) matching database → stamp; everything unregistered → refusal (`RuntimeError`, message keeps "recreate the database" guidance for unresolvable cases).
- Cross-plan: `plans/20261029-221254_dlqbox001_dlq-sqlite-outbox.md` sequences after this Plan (its outbox step registers later); compatible.

## Design decisions
- Refusal is the default; migration is the exception only when `plan()` resolves a unique registered path and the backup gate passes. A failed gate or failed step refuses startup unchanged (REQ-002/REQ-003/REQ-005).
- `_expected_schema_version`, `_matches_current_schema`, and the fingerprint call stay as the post-migration proof; the runner's injected verifier uses `scripts/shared/eventbus_schema_fingerprint.py::assert_matches` from row 02.

## Alternatives considered
- N/A: approach fixed by Plan Design (registered-path migration with unchanged refusal).

## Implementation
### Target file
- `scripts/eventbus/schema.py`

### Procedure
1. In `_init_schema`, replace the unconditional refusal branch (`schema.py:93-96`) with: resolve `REGISTRY` path from `found` toward `expected` via `MigrationRunner.plan(...)` from `shared.db_migrations`.
2. When a path resolves: run `apply(...)` with row 02's `verify_backup` gate and dry_run=False; on success re-run `assert_matches(conn)` and return.
3. When no path resolves (downgrade, cycle, unknown), raise the existing refusal error; when the gate or a step fails, propagate a refusal that leaves the database at its previous version.

### Method
Single-function change plus imports of `shared.db_migrations` and `eventbus.migrations`; keep the module docstring contract ("Create the schema when absent...") accurate by updating its wording to state registered-path migration.

### Details
- Import direction must stay `eventbus` → `shared` only (`lint-imports` `eventbus-is-isolated`).
- The unstamped (version 0) branch must not be routed through the migration runner — it is shape-verified stamping, not a registered migration.

## Compatibility considerations
- After row 04 lands, the expected version rises to 4; databases still at 3 take the registered bootstrap path instead of today's hard refusal. The refusal message for genuinely unsupported versions must still name "recreate the database".

## Security considerations
- No new input surface; migration SQL is repo-authored.

## Rollback considerations
- Revert the commit; startup falls back to the previous refuse-only behavior (databases already migrated to 4 would then be refused, matching the pre-change contract).

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_schema_version.py tests/eventbus/test_eventbus_migrations.py` (row 16 extends refusal/migration tests fail-first; row 15 covers registry behavior).
- `lint-imports`; `uv run mypy --no-namespace-packages scripts/`.

## Completion criteria
- A version-3 database starts successfully by migrating to 4 with a ledger row; a version-5, cyclic, or malformed database still refuses startup; dry-run of the same path mutates nothing (covered by row 15 tests).

## Out of Scope
- Registry definitions, CLI, baseline DDL, workflow domain (rows 02/04/05/06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Tests come from rows 15/16 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A for this row |

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
- **Requirement ID**: `REQ-003` (refusals), `REQ-005` (fail-closed startup), `REQ-009` (registered paths preserve rows)
- **Source issue**: `issues/20261029-104500_dbmig001_forward-only-db-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-214108_dbmig001_forward-only-db-migrations.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-071336
- **Related target files**: `scripts/eventbus/schema.py`
