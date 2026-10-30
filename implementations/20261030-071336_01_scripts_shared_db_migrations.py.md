## Goal
Create the domain-neutral forward-only migration framework in `scripts/shared/db_migrations.py` (new): registry-entry dataclass, runner, pre-migration gate, ledger primitives, dry-run, and refusal semantics, so `db` and `eventbus` share one migration lifecycle (REQ-001 migration framework, REQ-002 backup gate, REQ-003 refusal semantics, REQ-004 dry-run, REQ-006 ledger primitives).

## Scope
- In scope: `MigrationSpec` (new) registry entry (id, from_version, to_version, precondition checks, mutation SQL, postcondition fingerprint check), `MigrationRunner` (new) path resolution and execution, pre-migration gate (WAL checkpoint + SQLite backup-API copy + `PRAGMA integrity_check` + caller-supplied backup-verification callback), ledger read/write primitives for `schema_migrations` (new), dry-run mode, downgrade/cycle/unknown-path refusals.
- Out of scope: any domain registry content (rows 02, 06), startup wiring (row 03), CLIs (rows 05, 07), drills (row 11).

## Assumptions
- The framework lives in `scripts/shared/` because `.importlinter` contract `eventbus-is-isolated` forbids `eventbus` → `db`, and `shared-is-leaf` forbids `shared` → `db`; both layers may import `shared`. Precedent: `scripts/shared/eventbus_schema_fingerprint.py`, `scripts/shared/db_maintenance.py`.
- Because `shared` cannot import `scripts/db/recovery.py`, the runner performs only the generic `PRAGMA integrity_check` on the backup copy and receives domain-specific backup verification (domain identity, fingerprint) as an injected callable from the calling domain layer; the `db` layer passes a wrapper around `scripts/db/recovery.py::_backup_is_usable` (row 10 exposes it), the `eventbus` layer passes a wrapper around `scripts/shared/eventbus_schema_fingerprint.py::assert_matches`. This satisfies the Plan's reuse instruction without violating the import contract.
- Ledger table contract (Plan Design): `schema_migrations(id TEXT PRIMARY KEY, applied_at TEXT, from_version INTEGER, to_version INTEGER)`; versions are integers defined per domain registry. For `workflow.sqlite` the registry maps the string `WORKFLOW_SCHEMA_VERSION` (`"1.1.0"`, `scripts/db/schema_sql.py:25`) to an integer version code. Needs confirmation: the exact code mapping is decided in row 06's registry; owner veto per Plan UNK-02.
- Cross-plan overlaps involving this row: none; this file is unique to this Plan. Related sequencing (rows 02/04/05): `plans/20261029-221254_dlqbox001_dlq-sqlite-outbox.md` registers the first real forward step on top of this framework after this Plan lands (sequenced dependency, not a conflict).

## Design decisions
- Path resolution refuses, never repairs: no registered unique ordered forward path → typed refusal (downgrade / cycle / unknown), raised before any mutation (REQ-003).
- One transaction per migration step; on error the step rolls back and the database stays at the last ledger-recorded version; original files are never replaced by the runner (Plan Design failure-path invariant).
- Gate order: checkpoint (`PRAGMA wal_checkpoint`) → backup via `sqlite3.Connection.backup` into a temp copy → `PRAGMA integrity_check` → injected domain verification; a migration is refused without a passing gate (REQ-002).
- Dry-run executes resolution and the gate against a throwaway copy and mutates nothing (REQ-004).

## Alternatives considered
- Framework in `scripts/db/` with eventbus duplication — rejected: violates `eventbus-is-isolated` and duplicates the lifecycle.
- Runner importing `scripts/db/recovery.py` helpers directly — rejected: violates `shared-is-leaf`; injection keeps helpers reused from the domain layer instead.

## Implementation
### Target file
- `scripts/shared/db_migrations.py` (new)

### Procedure
1. Define `MigrationSpec` (new) frozen dataclass: `id: str`, `from_version: int`, `to_version: int`, `preconditions: tuple[Callable[[sqlite3.Connection], None], ...]`, `mutation_sql: str`, `postcondition: Callable[[sqlite3.Connection], None]`.
2. Define refusal types (new): `MigrationRefusalError` with subclasses/reasons `DOWNGRADE`, `UNKNOWN_PATH`, `CYCLE`, `NO_VERIFIED_BACKUP`.
3. Implement `MigrationRunner` (new): `plan(current_version, ledger_rows, registry)` resolves a unique ordered forward path or raises a refusal; `apply(conn, specs, backup_verifier, dry_run)` runs the gate then each step in its own transaction, writes the ledger row, re-checks the postcondition fingerprint, and rolls back the failing step only.
4. Implement ledger primitives (new): `ensure_ledger(conn)` (CREATE TABLE IF NOT EXISTS `schema_migrations` (new)), `read_ledger(conn)`, `record_applied(conn, spec)`.
5. Implement the gate helper: WAL checkpoint, backup copy via `sqlite3.connect(...).backup(...)` to a temp path, integrity check, injected verifier; temp copy is always closed and deleted (`try/finally`).

### Method
Additive new module only; no import from `db`, `eventbus`, `agent`, `rag`, or `mcp_servers` (stdlib only, like `scripts/shared/eventbus_schema_fingerprint.py`). Refusal-before-mutation and per-step transactions are the contract the domain rows (02, 03, 06) rely on.

### Details
- Ledger column contract per Plan Design; `applied_at` uses `strftime('%Y-%m-%dT%H:%M:%SZ','now')` style consistent with `scripts/db/schema_sql.py` defaults.
- The runner never calls `PRAGMA user_version` writes itself beyond what a registered step's SQL does; stamping is part of each step's mutation SQL so the ledger and fingerprint stay a single proof (REQ-006).
- Domain-agnostic: version comparison is plain integer comparison of `from_version`/`to_version`.

## Compatibility considerations
- New module; no existing importer. Must pass `lint-imports` (`shared-is-leaf`). `mypy --no-namespace-packages` clean.

## Security considerations
- No dynamic SQL from user input; mutation SQL comes only from registered specs authored in the repo. Backup copies must be created and cleaned under a temp dir (`tempfile`), never overwrite live DB files.

## Rollback considerations
- Revert the commit; no runtime state depends on the module until rows 02–07 wire it.

## Validation plan
- `uv run pytest tests/shared/test_db_migrations.py` (row 14's document writes these tests first — fail-first).
- `uv run mypy --no-namespace-packages scripts/` ; `lint-imports` ; `uv run python tools/check_db_separation.py`.

## Completion criteria
- Framework refuses downgrade/cycle/unknown paths before any mutation; an applied step records exactly one ledger row and passes its postcondition; dry-run leaves the target byte-identical; failure mid-step leaves the database at the last ledger-recorded version.

## Out of Scope
- Domain registries, CLIs, startup wiring, drills, docs (separate rows of the same Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Tests come from row 14's procedure document |
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
- **Requirement ID**: `REQ-001` (migration framework), `REQ-002` (backup gate), `REQ-003` (refusals), `REQ-004` (dry-run), `REQ-006` (ledger)
- **Source issue**: `issues/20261029-104500_dbmig001_forward-only-db-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-214108_dbmig001_forward-only-db-migrations.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-071336
- **Related target files**: `scripts/shared/db_migrations.py`
