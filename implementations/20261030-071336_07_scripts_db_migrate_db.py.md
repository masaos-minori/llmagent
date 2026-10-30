## Goal
Create the `workflow.sqlite` migration CLI `scripts/db/migrate_db.py` (new) with `--dry-run`, `--apply`, and `--status` operating through the shared framework and the workflow registry, doubling as the drill-adjacent migration status command (REQ-001 migration framework, REQ-002 backup gate, REQ-004 dry-run, REQ-006 ledger status).

## Scope
- In scope: operator CLI entry point for the workflow domain only.
- Out of scope: registry content (row 06), framework internals (row 01), create-path wiring (row 08), drill harness (row 11).

## Assumptions
- No migration CLI exists today: `scripts/db/create_schema.py` is the only schema entry point (its `__main__` block runs the four create functions; a version mismatch raises, `create_schema.py:144-155`). This module is new, not a replacement of any existing script.
- DB path resolution uses the `db` layer's own configuration (`db.config.build_db_config` / `SQLiteHelper("workflow")`), the same mechanism `create_schema.py` and `rotation.py` use.
- No service-listener guard is needed for the workflow domain (unlike the eventbus CLI in row 05: the workflow database is embedded in the agent process, not behind a listening service); the CLI instead relies on SQLite busy/lock handling and refuses when the exclusive step fails.

## Design decisions
- Same CLI contract as row 05 for operator ergonomics: `--dry-run` resolves and gates against a throwaway copy without mutating; `--apply` requires a passing gate (row 06 `verify_backup`); `--status` prints `schema_migrations` rows and the current ledger version via row-01 ledger primitives plus the legacy `workflow_schema_version` marker for cross-checking.
- Exit codes distinguish refusal classes (0 success/no-op, 1 gate/step failure, 2 downgrade/unknown/cycle refusal); tests assert classes, not raw numbers (mirrors row 05).

## Alternatives considered
- Extending `create_schema.py` with CLI flags — rejected: the Plan separates startup validation (row 08) from the explicit operator entry point, and `create_schema.py` must stay importable with no argparse surface.

## Implementation
### Target file
- `scripts/db/migrate_db.py` (new)

### Procedure
1. `argparse` interface: `--dry-run`, `--apply`, `--status`, optional `--archive-dir` passthrough for the gate's backup copy location.
2. Compose `MigrationRunner` (row 01) + `db.migrations_workflow.REGISTRY` + `verify_backup` (row 06); report the resolved path or refusal reason.
3. `--status` output is machine-readable (stable field names) because row 11's drill harness reports ledger state next to drill artifacts.

### Method
New executable module in the `db` layer, `if __name__ == "__main__"` entry, mirroring `create_schema.py`'s logging/exit conventions. Land after rows 01 and 06 in `seq` order.

### Details
- Deployed invocation is `PYTHONPATH=/opt/llm/scripts python /opt/llm/scripts/db/migrate_db.py ...` (same invocation style as `deploy/init_db.sh:34`).

## Compatibility considerations
- New entry point; no existing importers. `.importlinter` db-layer contracts must stay KEPT.

## Security considerations
- No dynamic SQL; refuses writes when a step cannot complete; backup copies land in the configured archive area, not in ad-hoc paths.

## Rollback considerations
- Revert the commit; no runtime dependency until deployment references it (row 13 documents invocation).

## Validation plan
- `uv run pytest tests/db/test_migrations_workflow.py` (row 17 covers CLI incl. fault injection between backup and migration).
- `lint-imports`; `uv run mypy --no-namespace-packages scripts/`.

## Completion criteria
- `--dry-run` on a ledger-less baseline database reports the `workflow_ledger_baseline` path and leaves files byte-identical; `--apply` produces the baseline ledger row; an unmapped string version exits with the refusal class; `--status` shows ledger rows and the marker cross-check.

## Out of Scope
- Eventbus CLI (row 05), drills (row 11), docs invocation text (row 23).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Tests come from row 17 |
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
- **Requirement ID**: `REQ-001` (migration framework), `REQ-002` (backup gate), `REQ-004` (dry-run), `REQ-006` (ledger status)
- **Source issue**: `issues/20261029-104500_dbmig001_forward-only-db-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-214108_dbmig001_forward-only-db-migrations.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-071336
- **Related target files**: `scripts/db/migrate_db.py`
