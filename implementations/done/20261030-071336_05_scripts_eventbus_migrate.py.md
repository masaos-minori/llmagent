## Goal
Create the `eventbus.sqlite` migration CLI `scripts/eventbus/migrate.py` (new) with `--dry-run`, `--apply`, and `--status` operating through the shared framework and the EventBus registry (REQ-001 migration framework, REQ-002 backup gate, REQ-004 dry-run, REQ-006 ledger status).

## Scope
- In scope: operator CLI entry point only.
- Out of scope: registry content (row 02), startup wiring (row 03), framework internals (row 01).

## Assumptions
- The CLI refuses to run while the EventBus service holds the database: check the configured port (8015) via `ss -ltnpH 'sport = :8015'` or equivalent and abort if a listener exists (Plan Risk mitigation). Needs confirmation: none — fixed by the Plan.
- Exit codes distinguish refusal classes: 0 success/no-op, 1 gate/step failure, 2 refusal (downgrade/unknown/cycle), 3 service-holding-db refusal — exact mapping decided in implementation; tests assert classes, not raw numbers.
- Cross-plan: dlqbox001 will exercise this CLI for its outbox step after this Plan lands (sequenced).

## Design decisions
- `--dry-run` runs resolution and the full gate against a throwaway copy and mutates nothing (REQ-004); `--apply` requires a passing gate; `--status` prints ledger rows read via row-01 ledger primitives.
- DB path resolved through the EventBus layer's own configuration, not by importing `scripts/db/` (import contract).

## Alternatives considered
- One shared CLI for all domains — rejected: import contract forbids `eventbus` → `db`; per-domain CLIs keep each layer self-contained.

## Implementation
### Target file
- `scripts/eventbus/migrate.py` (new)

### Procedure
1. `argparse` interface: subcommands or flags for `--dry-run`, `--apply`, `--status`.
2. Compose `MigrationRunner` (row 01) + `eventbus.migrations.REGISTRY` + `verify_backup` (row 02); run gate; report resolved path or refusal reason.
3. Service-busy precheck before any mutation mode (`--apply`, `--dry-run` gate copy may read the live file; refuse mutation while the service listens).

### Method
New executable module mirroring the per-concern module style of `scripts/eventbus/` (`schema.py`, `dlq.py`); `if __name__ == "__main__"` entry.

### Details
- `MigrationRunner`, `MigrationSpec`, ledger primitives, `REGISTRY`, `verify_backup` are created by rows 01/02; this document assumes they exist in `seq` execution order (noted in Assumptions per Step 3c rule 2).

## Compatibility considerations
- None for existing importers (new entry point). `eventbus-is-isolated` must stay KEPT.

## Security considerations
- No dynamic SQL; refuses writes while another process holds the DB (single-writer assumption per ADR-008).

## Rollback considerations
- Revert the commit; no runtime dependency until deployment references it (row 13).

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_migrations.py` (row 15 covers CLI incl. fault injection between backup and migration).
- `lint-imports`; `uv run mypy --no-namespace-packages scripts/`.

## Completion criteria
- `--dry-run` on a version-3 database reports the `3 → 4` path and leaves files byte-identical; `--apply` produces ledger row `eventbus_ledger_baseline` and version 4; a downgrade/unknown target exits with the matching refusal class; mutation is refused while a service listener exists.

## Out of Scope
- Workflow CLI (row 07), drills (row 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261030-100000 | 20261030-100000 | Created scripts/eventbus/migrate.py: argparse --dry-run/--apply/--status via shared runner + REGISTRY + verify_backup; port-8015 service-busy guard; exit classes OK=0/gate-fail=1/refusal(downgrade/unknown/cycle)=2/service-busy=3. |
| 2 | Add or update tests per Validation plan | Completed | 20261030-100000 | 20261030-100000 | Tests come from row 15 CLI coverage is row 15 (subprocess fixtures incl. fault injection + port-guard); hand smoke test here covers --status/--dry-run/--apply/port-guard/exit-class mapping. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-100000 | 20261030-100000 | ruff format+check clean; mypy(444) clean; lint-imports 6/6; check_db_separation + check_docstrings clean. Hand smoke: v3->v4 apply writes ledger row + preserves events; dry-run byte-identical; listener on 8015 -> exit 3; downgrade/unknown/cycle -> exit 2; gate fail -> exit 1. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261030-100000 | 20261030-100000 | N/A for this row N/A: no docs/00_index.md task-scope mapping for migrate.py. |

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
- **Related target files**: `scripts/eventbus/migrate.py`