## Goal

Create the domain-neutral forward-only migration framework in `scripts/shared/db_migrations.py` (`REQ-001`, ordered registry and runner; `REQ-002`, verified-backup gate; `REQ-003`, refusals and intact original; `REQ-004`, dry-run; `REQ-006`, ledger).

## Scope

- Create only `scripts/shared/db_migrations.py`.
- Domain registries, CLIs, DDL, and startup wiring are other rows.

## Assumptions

- Step 3a correction (Plan, 2026-10-30): the Plan wrote `shared/db_migrations.py`; the importable root is `scripts/` (the `.importlinter` root packages), so the file is `scripts/shared/db_migrations.py`, and the Plan was corrected.
- Step 3a correction: `workflow.sqlite` has no `PRAGMA user_version`; its version is the text of the latest `workflow_schema_version` row (`WORKFLOW_SCHEMA_VERSION = "1.1.0"`, `scripts/db/schema_sql.py`), while `eventbus.sqlite` uses `PRAGMA user_version = 3`. The framework therefore takes a per-domain version accessor and stores versions as text; the Plan's `INTEGER` ledger columns became `TEXT`.
- `shared` is a leaf layer (`.importlinter` contract `shared-is-leaf`): this module imports the standard library and `shared.eventbus_schema_fingerprint` only (that module already imports only the standard library).
- `build_fingerprint(conn)` in `scripts/shared/eventbus_schema_fingerprint.py` is connection-based and reusable for any DDL applied to an in-memory database; only `apply_schema_in_memory` is EventBus-specific. The framework reuses `build_fingerprint` and does not duplicate it.
- No migration is registered at landing; the first consumers are `toolexec001`, `dlqbox001`, and the schema rows of wfrecovery001 and wftaskapi001. Execution order follows the Plan's `Implementation steps` phases (this row is in Phase 1, first), not necessarily the table `seq`.

## Design decisions

- One frozen `MigrationSpec` (new) dataclass: `migration_id`, `from_version` (new), `to_version` (new) (text), `apply` (callable on a connection), optional `precondition` and `postcondition` callables.
- One frozen `MigrationDomain` (new) dataclass bundles the domain name, `read_version` (new), `write_version` (new), and `verify_shape(conn, version)` callables, so the runner never knows whether the version lives in `PRAGMA user_version` or in a table.
- Typed refusals: `MigrationError` (new) base (a `RuntimeError`), `MigrationRefusedError` (new) for downgrade, unknown path, ambiguous path, and missing verified backup, `MigrationFailedError` (new) for a failed step.
- Each step runs in one `BEGIN IMMEDIATE` transaction that applies the change, writes the new version and the ledger row, runs the postcondition and shape check, and only then commits; any exception rolls back.

- Correction (Step 3b, user decision 2026-10-30): `tests/mcp_servers/mdq/test_mdq_rag_boundary.py::test_shared_layer_has_no_direct_mdq_rag_sqlite_access` forbids the text `sqlite3.connect` in `scripts/shared/` (only `eventbus_schema_fingerprint.py` is allowlisted). The framework therefore never opens database files itself: `MigrationDomain` has a required `connect` field (a callable opening a path), `create_verified_backup` takes `connect`, and each domain registry (rows 02 and 06) supplies it. The test file stays unmodified.

## Alternatives considered

- Version resolution by a generic graph search over specs: rejected, a unique linear chain is enough and ambiguity is a refusal.
- Putting the framework in `scripts/db/`: rejected, `eventbus` may not import `db` (`eventbus-is-isolated`).

## Implementation

### Target file

`scripts/shared/db_migrations.py` (new)

### Procedure

1. Add the ledger DDL constant `LEDGER_DDL` (new) for `schema_migrations(id TEXT PRIMARY KEY, applied_at TEXT NOT NULL, from_version TEXT NOT NULL, to_version TEXT NOT NULL)`, plus `ensure_ledger` (new)(conn) that creates it idempotently and `read_ledger` (new)(conn) returning the applied ids in order.
2. Add `resolve_path` (new)(specs, current, target) returning the ordered specs; raise `MigrationRefusedError` (new) for a downgrade, an unknown current or target version, a missing hop, two specs from one version, or a cycle.
3. Add `create_verified_backup` (new)(db_path, backup_dir) that runs `PRAGMA wal_checkpoint(TRUNCATE)` on the source, copies it with the `sqlite3` backup API (the approach of `_archive_db_file` in `scripts/db/rotation.py`), runs `PRAGMA integrity_check` on the copy, and raises `MigrationRefusedError` (new) when the copy is not `ok`; return the backup path.
4. Add `run_migrations` (new)(db_path, domain, specs, target_version, backup_dir, dry_run=False) returning a `MigrationReport` (new) dataclass (applied ids, backup path, dry_run flag, from and to versions): resolve the path first (a no-op path returns an empty report), then back up, then apply each step.
5. Dry-run: copy the database to a temporary file, run the whole sequence on the copy, delete the copy, and leave the original byte-identical; the report says `dry_run=True`.

### Method

- `run_migrations` (new) opens its own connection with `isolation_level=None` and issues `BEGIN IMMEDIATE`/`COMMIT`/`ROLLBACK` explicitly so DDL and the ledger row share one transaction.
- A failed step raises `MigrationFailedError` (new) carrying the migration id, after rollback; the database stays at the last ledger-recorded version.
- The backup is created before the first step, never when the path is a no-op, and its path is returned in the report so callers can record it (AC-4).

### Details

- Version stamping of an unstamped database (version 0 or no version row) is a domain concern (rows 02 and 06); the framework only reads through `read_version` (new).
- Keep the module under the 20480 B gate of `tools/check_module_size.py`; split the ledger helpers if it grows past it.

## Compatibility considerations

- New module; no caller changes.
- A `RuntimeError` subclass hierarchy keeps broad `except RuntimeError` startup handlers working.

## Security considerations

- Only parameterized SQL for ledger values; the version and table names come from code, not user input (B608 suppressions need a justification per `rules/coding.md`).
- Backup and temporary-copy paths are caller-supplied; the runner never deletes anything except its own dry-run copy.

## Rollback considerations

- N/A: new module; revert the commit. No caller exists until later rows.

## Validation plan

- `uv run pytest tests/shared/test_db_migrations.py -v` (row 14 document)
- `uv run ruff format scripts/shared/db_migrations.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`
- `uv run python tools/check_db_separation.py`

## Completion criteria

- `scripts/shared/db_migrations.py` defines the specs, domain, ledger helpers, resolver, verified backup, and runner above and imports no `db`, `eventbus`, or `agent` module.
- A downgrade, an unknown path, and a missing verified backup each raise `MigrationRefusedError` (new); a failing step raises `MigrationFailedError` (new) and leaves the original database intact.
- Dry-run leaves the database byte-identical.

## Out of Scope

- Domain registries, CLIs, startup wiring, DDL, and tests (other rows).
- Automatic restore from the backup on failure (Plan Out-of-Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the framework per Procedure/Method/Details | Completed | 20261030-162046 | 20261030-162046 | Plan Phase 1 scripts/shared/db_migrations.py created; connect injected via MigrationDomain (Step 3b, user decision); also errors.py docstring header fixed |
| 2 | Add or update tests per Validation plan | Completed | 20261030-162046 | 20261030-162046 | Covered by the row 14 document tests/shared/test_db_migrations.py (row 14) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-162046 | 20261030-162046 | ruff/mypy/lint-imports/bandit/module-size/db-separation passed; full suite 10468 passed; coverage 96% |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-006
- **Source issue**: issues/20261029-104500_dbmig001_forward-only-db-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-214108_dbmig001_forward-only-db-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-151746
- **Related target files**: scripts/shared/db_migrations.py