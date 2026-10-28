# Procedure: add the partial unique index on redelivered_from and bump the schema version

## Goal

Make SQLite enforce at most one descendant per original event and stamp schema version 2 (Plan REQ-001).

## Scope

- Modify only `scripts/eventbus/schema.sql`.
- In scope: one `CREATE UNIQUE INDEX` statement and the `PRAGMA user_version` line.
- Out of scope: a migration (ADR-008: recreate on schema change), `schema.py`, tests, docs.

## Assumptions

- Ordering note: write the failing tests (rows 3-5) first.
- `schema.sql` is the single DDL source for `eventbus.schema`, `db.schema_sql` and the shared fingerprint, so one edit reaches all three.
- A version-1 database is refused at startup by `_init_schema` with "recreate the database"; this is the documented upgrade path (UNK-01).
- Overlap (compatible): `plans/done/20261028-093931_adrgate005_enforce-adr-evidence-checks.md` (archived, procedures pending) also targets the ADR-006 file; it renames two stale test citations in the Verification table while this procedure edits Implementation Notes only. Any citation added here must resolve to an existing test node once that Plan's node validation is in force.

## Design decisions

- Partial unique index `WHERE redelivered_from IS NOT NULL` so the many NULL-source events stay unconstrained; name `idx_events_redelivered_from` (new) follows the existing naming.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`scripts/eventbus/schema.sql`

### Procedure

- After `CREATE INDEX IF NOT EXISTS idx_events_dlq_seq ON events(dlq_at, seq);` add `CREATE UNIQUE INDEX IF NOT EXISTS idx_events_redelivered_from ON events(redelivered_from) WHERE redelivered_from IS NOT NULL;`.
- Change `PRAGMA user_version = 1;` to `PRAGMA user_version = 2;`; keep the comment above it.

### Method

Add one statement and change one number.

### Details

- `eventbus_schema_version()` in `scripts/db/schema_sql.py` and `_expected_schema_version` in `scripts/eventbus/schema.py` read the stamp from this file by regex, so no code change is needed.
- Run `uv run python tools/check_db_separation.py` after a schema DDL change (`routing.md`).

## Compatibility considerations

- Existing `eventbus.sqlite` files (version 1) are refused at startup until recreated; the docs give the operator procedure and the deploy hand-off requires a backup and the owner's go-ahead (UNK-01, UNK-02).

## Security considerations

- Strengthens an integrity constraint; no new input handling.

## Rollback considerations

- Revert the commit; databases already recreated at version 2 would then be refused at version mismatch and need recreation again.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_schema_version.py tests/db/test_create_schema.py tests/deploy/test_init_db_eventbus_schema.py -q` | Pass |
| 2 | `uv run ruff format scripts/eventbus/schema.sql`; `uv run ruff check scripts/eventbus/schema.sql`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/eventbus/schema.sql -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |
| 4 | `uv run python tools/check_db_separation.py` | No finding |

## Completion criteria

- `schema.sql` defines the partial unique index and stamps version 2; a new database has both.

## Out of Scope

- Migration code, other tables.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (database-level uniqueness of the redelivery source; version 2)
- **Source issue**: issues/20261027-155850_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-094441_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-120147
- **Related target files**: scripts/eventbus/schema.sql
