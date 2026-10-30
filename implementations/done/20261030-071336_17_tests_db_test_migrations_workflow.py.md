# Implementation Procedure: `tests/db/test_migrations_workflow.py` (workflow registry + CLI tests)

## Goal
Create coverage for the workflow migration registry and the `workflow.sqlite` migration CLI including fault injection (Plan row 17; REQ-002, REQ-003, REQ-009).

## Scope
- In scope: `scripts/db/migrations_workflow.py` (row 06) and `scripts/db/migrate_db.py` (row 07) against file-based workflow-shaped fixtures.
- Out of scope: shared framework internals (row 14), create-path bootstrap (row 18), drills (row 19).

## Assumptions
- Fixtures build `workflow.sqlite` files by executing `build_workflow_schema_sql()` output (minus the ledger DDL) to reproduce the legacy shape (string `workflow_schema_version` marker only), re-verified anchor: `scripts/db/schema_sql.py:168-218`.
- No service listener guard for workflow (row 07 contract); busy/lock refusal is exercised with a held write connection in-test.

## Design decisions
- The legacy bootstrap `workflow_ledger_baseline` (`1 → 1`, row 06) is the primary migration test — it is the only registered workflow step at landing, and AC-1 coverage for this domain runs through it.
- CLI via subprocess argv; ledger status parsed from `--status` output.

## Alternatives considered
- In-process runner tests only — rejected: the Plan's test matrix names this file for CLI + integration coverage (`uv run pytest tests/db`).

## Implementation
### Target file
- `tests/db/test_migrations_workflow.py` (new)

### Procedure
1. Fixtures: legacy workflow DB (no ledger, `workflow_schema_version` row `"1.1.0"`), workflow DB with unmapped string version `"2.0.0"`, populated `tasks`/`attempts` rows for preservation checks.
2. Tests:
   - Bootstrap: 1→1 gate-gated migration creates `schema_migrations`, writes the baseline row, preserves all rows and the unchanged string marker (REQ-009/AC-1).
   - Refusals: unmapped string version refused with no mutation (file hash unchanged); double bootstrap refused via the registered chain check and ledger uniqueness; downgrade request refused.
   - Fault injection: corrupt the checkpoint backup before gate → refusal before live mutation (REQ-002/AC-4); step-hook failure mid-migration leaves DB at pre-step state.
   - CLI dry-run leaves the fixture byte-identical (AC-5).
   - CLI apply followed by status prints the baseline ledger row.
   - A busy DB (connection held in-test) produces the refusal exit class.
3. Ledger rows asserted with ISO-8601 `applied_at`.

### Method
pytest + tmp_path + subprocess argv per `rules/coding.md`.

### Details
- Legacy-shape fixtures strip the ledger DDL from `build_workflow_schema_sql()` output at fixture build time.

## Compatibility considerations
- New file only. Workflow store (`scripts/agent/workflow/state_store.py`) untouched — regression that normal engine access still works after bootstrap is covered by existing agent workflow tests staying green.

## Security considerations
- No production DB access.

## Rollback considerations
- Delete the file.

## Validation plan
- Automated: `uv run pytest tests/db/test_migrations_workflow.py` (fails before rows 06/07 land, passes after); `uv run pytest tests/db` stays green.
- Manual: none.

## Completion criteria
- Bootstrap preserves rows and marker; refusals pre-mutation; dry-run byte-identity; `--status` ledger output stable.

## Out of Scope
- Engine startup schema check changes (`scripts/agent/services/workflow_schema.py` is out of the Plan's target set; REQ-005 satisfaction there is asserted by existing tests staying green).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Wrote tests/db/test_migrations_workflow.py (18 tests): registry/path, bootstrap+preservation, resume, refusals (unknown/downgrade/unmapped/checkpoint/bad-backup/verify_backup), failing-step rollback, dry-run byte-identity, plus 6 subprocess CLI tests. |
| 2 | Add or update tests per Validation plan | Completed | — | — | 18/18 pass; tests/db 362 pass; ruff/bandit/ast-grep/lint-imports clean; no new mypy regressions. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff format+check clean; lint-imports 6 KEPT; bandit 0 med/high; ast-grep bare-except clean; pytest tests/db 362 passed. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | Out of scope: new file only; no docs/ADR touched. |

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
- **Related target files**: `tests/db/test_migrations_workflow.py`
- **Generated at**: 20261030-071336